import express from 'express';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const app = express();
const PORT = 3001;

app.use(express.json());

// 保存先ディレクトリ
const dataDir = path.join(__dirname, '..', 'data');
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

const APP_ID = process.env.RAKUTEN_APP_ID;
const ACCESS_KEY = process.env.RAKUTEN_ACCESS_KEY;
// 新しいエンドポイント
const CATEGORY_LIST_URL = 'https://openapi.rakuten.co.jp/recipems/api/Recipe/CategoryList/20170426';
const CATEGORY_RANKING_URL = 'https://openapi.rakuten.co.jp/recipems/api/Recipe/CategoryRanking/20170426';

/**
 * カテゴリ一覧を取得
 */
async function fetchCategoryList() {
  const url = `${CATEGORY_LIST_URL}?format=json&applicationId=${encodeURIComponent(APP_ID)}&accessKey=${encodeURIComponent(ACCESS_KEY)}`;
  console.log('リクエストURL:', url);
  const res = await fetch(url);
  if (!res.ok) {
    const body = await res.text();
    console.error('APIレスポンス:', res.status, body);
    throw new Error(`カテゴリ一覧の取得に失敗: ${res.status} - ${body}`);
  }
  return res.json();
}

/**
 * キーワードに一致するカテゴリを検索
 */
function searchCategories(categoryData, keyword) {
  const matched = [];

  // 大カテゴリ
  for (const cat of categoryData.result.large) {
    if (cat.categoryName.includes(keyword)) {
      matched.push({ categoryId: String(cat.categoryId), categoryName: cat.categoryName, type: 'large' });
    }
  }

  // 中カテゴリ
  for (const cat of categoryData.result.medium) {
    if (cat.categoryName.includes(keyword)) {
      matched.push({
        categoryId: `${cat.parentCategoryId}-${cat.categoryId}`,
        categoryName: cat.categoryName,
        type: 'medium'
      });
    }
  }

  // 小カテゴリ
  for (const cat of categoryData.result.small) {
    if (cat.categoryName.includes(keyword)) {
      matched.push({
        categoryId: `${cat.parentCategoryId}-${cat.categoryId}`,
        categoryName: cat.categoryName,
        type: 'small'
      });
    }
  }

  return matched;
}

/**
 * カテゴリIDからランキングレシピを取得
 */
async function fetchCategoryRanking(categoryId) {
  const url = `${CATEGORY_RANKING_URL}?format=json&applicationId=${encodeURIComponent(APP_ID)}&accessKey=${encodeURIComponent(ACCESS_KEY)}&categoryId=${encodeURIComponent(categoryId)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`ランキング取得失敗 (categoryId: ${categoryId}): ${res.status}`);
  return res.json();
}

/**
 * レシピ検索 API
 * POST /api/search  body: { keyword: "..." }
 */
app.post('/api/search', async (req, res) => {
  const { keyword } = req.body;

  if (!keyword || typeof keyword !== 'string' || keyword.trim() === '') {
    return res.status(400).json({ error: 'キーワードを入力してください' });
  }

  if (!APP_ID || !ACCESS_KEY) {
    return res.status(500).json({ error: 'RAKUTEN_APP_ID または RAKUTEN_ACCESS_KEY が設定されていません。.env ファイルを確認してください。' });
  }

  const sanitizedKeyword = keyword.trim();

  try {
    // 1. カテゴリ一覧取得
    const categoryData = await fetchCategoryList();

    // 2. キーワードでカテゴリ検索
    const matchedCategories = searchCategories(categoryData, sanitizedKeyword);

    if (matchedCategories.length === 0) {
      return res.json({ keyword: sanitizedKeyword, categories: [], recipes: [], message: '一致するカテゴリが見つかりませんでした' });
    }

    // 3. 各カテゴリのランキングレシピを取得（最大5カテゴリ）
    const targetCategories = matchedCategories.slice(0, 5);
    const allRecipes = [];

    for (const cat of targetCategories) {
      try {
        const rankingData = await fetchCategoryRanking(cat.categoryId);
        if (rankingData.result) {
          for (const recipe of rankingData.result) {
            allRecipes.push({
              recipeId: recipe.recipeId,
              recipeTitle: recipe.recipeTitle,
              recipeDescription: recipe.recipeDescription,
              foodImageUrl: recipe.foodImageUrl,
              recipeMaterial: recipe.recipeMaterial,
              recipeUrl: recipe.recipeUrl,
              recipePublishday: recipe.recipePublishday,
              shop: recipe.shop,
              pickup: recipe.pickup,
              recipeCost: recipe.recipeCost,
              recipeIndication: recipe.recipeIndication,
              categoryName: cat.categoryName,
              categoryId: cat.categoryId,
            });
          }
        }
      } catch (e) {
        console.error(`カテゴリ ${cat.categoryName} のランキング取得エラー:`, e.message);
      }
    }

    // 4. 結果を構築
    const result = {
      keyword: sanitizedKeyword,
      fetchedAt: new Date().toISOString(),
      categories: targetCategories,
      totalRecipes: allRecipes.length,
      recipes: allRecipes,
    };

    // 5. .json ファイルとして保存
    const timestamp = Date.now();
    const safeKeyword = sanitizedKeyword.replace(/[<>:"/\\|?*]/g, '_');
    const fileName = `${safeKeyword}_${timestamp}.json`;
    const filePath = path.join(dataDir, fileName);
    fs.writeFileSync(filePath, JSON.stringify(result, null, 2), 'utf-8');

    console.log(`保存完了: ${filePath}`);

    return res.json({ ...result, savedFile: fileName });
  } catch (err) {
    console.error('検索エラー:', err);
    return res.status(500).json({ error: 'レシピ検索中にエラーが発生しました', details: err.message });
  }
});

/**
 * 保存済みファイル一覧
 */
app.get('/api/files', (req, res) => {
  const files = fs.readdirSync(dataDir).filter(f => f.endsWith('.json'));
  res.json({ files });
});

app.listen(PORT, () => {
  console.log(`サーバー起動: http://localhost:${PORT}`);
});

import { useState } from 'react'
import './App.css'
import TipsBoard from './Components/TipsBoard'
import PostTip from './Components/PostTip';

function App() {
  const [inputWord, setInputWord] = useState("");
  const [confirmedWord, setConfirmedWord] = useState("");
  const [isDisplay, setIsDisplay] = useState(false);
  const [isPop, setIsPop] = useState(false);
  const [recipes, setRecipes] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");

  const onInputKeyDown = async (e) => {
    if (e.key === 'Enter' && inputWord.trim() !== '') {
      setConfirmedWord(inputWord);
      setIsDisplay(true);
      setIsLoading(true);
      setMessage("");

      try {
        const res = await fetch('/api/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ keyword: inputWord.trim() }),
        });
        const data = await res.json();

        if (res.ok) {
          setRecipes(data.tips || []);
          if (data.tips && data.tips.length > 0) {
            setMessage(`${data.totalResults}件のTipsが見つかりました`);
          } else {
            setMessage(data.message || 'ヒットがありません');
          }
        } else {
          setMessage(data.detail || 'エラーが発生しました');
        }
      } catch (err) {
        setMessage('サーバーに接続できません。サーバーが起動しているか確認してください。');
      } finally {
        setIsLoading(false);
      }
    }
  };

  const resetPage = () => {
    setInputWord("");
    setConfirmedWord("");
    setIsDisplay(false);
    setRecipes([]);
    setMessage("");
  };

  return (
    <>
      <h1 
      onClick={resetPage}
      className='pageTitle'
      >Tip's Tips</h1>
      <h2>暮らしに小さな幸せを</h2>
      <input
       type="text" 
       value={inputWord}
       onChange={ (e) => setInputWord(e.target.value)}
       onKeyDown={onInputKeyDown}
       placeholder='食材・料理名を入力してEnter'
      />
      {isLoading && <p>検索中...</p>}
      {message && <p className="searchMessage">{message}</p>}
      <h2>確定:{confirmedWord}</h2>
      <button onClick={()=>setIsPop(true)}>編集を開く</button>
      <PostTip isPop={isPop} setIsPop={setIsPop}></PostTip>
      <TipsBoard isDisplay={isDisplay} recipes={recipes}></TipsBoard>
    </>
  )
}

export default App

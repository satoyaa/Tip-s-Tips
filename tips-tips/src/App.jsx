import { useState, useEffect } from 'react'
import { SquarePen } from "lucide-react";

import './App.css'
import SortControls from './Components/SortControls';
import TipsBoard from './Components/TipsBoard'
import PostTip from './Components/PostTip';

function App() {
  const [inputWord, setInputWord] = useState("");
  const [confirmedWord, setConfirmedWord] = useState("");
  const [isDisplay, setIsDisplay] = useState(false);
  const [isPop, setIsPop] = useState(false);
  const [tips, setTips] = useState([]);
  const [sortBy, setSortBy] = useState("");


  useEffect(() => {
    const fetchTips = async () => {
      // 検索／ソートのパラメータを組み立て
      const url = new URL(`${import.meta.env.VITE_API_URL}/tips`);
      if (confirmedWord) {
        url.searchParams.append("tag", confirmedWord);
      }
      if (sortBy === "likes") {
        url.searchParams.append("sort", "likes");
        url.searchParams.append("order", "desc");
      }

      try {
        const response = await fetch(url);
        const data = await response.json();
        setTips(data);
      } catch (error) {
        console.error("Failed to fetch tips:", error);
      }
    };

    // 入力中のリクエスト過多を防ぐ
    const timer = setTimeout(() => {
      fetchTips();
    }, 300);

    return () => clearTimeout(timer);
  }, [confirmedWord, sortBy]); // 入力・ソート条件が変わるたびに実行

  const onInputKeyDown = (e) => {
    if (e.key === 'Enter') {
      setConfirmedWord(inputWord);
      setIsDisplay(true);
    }
  };

  //ページをリセット，すべてのstateは初期値に
  //リセットでもconfirmedWordの更新判定になるので何とかしたい
  //不要なリクエストが発生してる
  const resetPage = () => {
    setInputWord("");
    setConfirmedWord("");
    setTips([]);
    setIsDisplay(false);
    setSortBy("");
  };

  return (
    <>
      <h1 
      onClick={resetPage}
      className='pageTitle'
      >Tip's Tips</h1>
      <h2 className='pageSubTitle'>～いつもの暮らしをちょっと豊かに～</h2>
      <input
       type="text" 
       value={inputWord}
       onChange={ (e) => setInputWord(e.target.value)}
       onKeyDown={onInputKeyDown}
       placeholder='幸せを探す'
       className='customInput'
      />
      <button className='postOpenButton' onClick={()=>setIsPop(true)}>
        <SquarePen
        size={50}        // サイズ
        color="#ffffff"    // 色
        strokeWidth={2}  // 線の太さ
        />
      </button>
      
      <PostTip isPop={isPop} setIsPop={setIsPop}></PostTip>

      {/* 人気順ソート */}
      <SortControls sortBy={sortBy} setSortBy={setSortBy} />

      <TipsBoard isDisplay={isDisplay} tips={tips} setTips={setTips}></TipsBoard>
    </>
  )
}

export default App

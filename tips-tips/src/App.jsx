import { useState, useEffect } from 'react'
import { SquarePen } from "lucide-react";

import './App.css'
import TipsBoard from './Components/TipsBoard'
import PostTip from './Components/PostTip';
import PopularTipsGrid from './Components/PopularTipsGrid';

function App() {
  const [inputWord, setInputWord] = useState("");
  const [confirmedWord, setConfirmedWord] = useState("");
  const [isDisplay, setIsDisplay] = useState(false);
  const [isPop, setIsPop] = useState(false);
  const [tips, setTips] = useState([]);

  useEffect(() => {
    if (!confirmedWord) {
      return;
    }

    const fetchTips = async () => {
      const url = new URL(`${import.meta.env.VITE_API_URL}/tips`);
      url.searchParams.append("tag", confirmedWord);

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
  }, [confirmedWord]); // 入力が確定されるたびに実行

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

      {isDisplay ? (
        <TipsBoard
          isDisplay={true}
          tips={tips}
          setTips={setTips}
          layout="free"
        />
      ) : (
        <PopularTipsGrid />
      )}
    </>
  )
}

export default App

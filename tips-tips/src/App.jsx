import { useState } from 'react'
import './App.css'
import TipsBoard from './Components/TipsBoard'
import PostTip from './Components/PostTip';

function App() {
  const [inputWord, setInputWord] = useState("");
  const [confirmedWord, setConfirmedWord] = useState("");
  const [isDisplay, setIsDisplay] = useState(false);
  const [isPop, setIsPop] = useState(false);

  const onInputKeyDown = (e) => {
    if (e.key === 'Enter') {
      setConfirmedWord(inputWord);
      setIsDisplay(true);
    }
  };

  const resetPage = () => {
    setInputWord("");
    setConfirmedWord("");
    setIsDisplay(false);
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
       placeholder='文字を入力'
      />
      <h2>確定:{confirmedWord}</h2>
      <button onClick={()=>setIsPop(true)}>編集を開く</button>
      <PostTip isPop={isPop} setIsPop={setIsPop}></PostTip>
      <TipsBoard isDisplay={isDisplay}></TipsBoard>
    </>
  )
}

export default App

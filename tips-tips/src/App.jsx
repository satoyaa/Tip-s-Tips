import { useState } from 'react'
import './App.css'
import TipsBoard from './Components/TipsBoard'

function App() {
  const [inputWord, setInputWord] = useState("")

  return (
    <>
      <h1>Tip's Tips</h1>
      <h2>暮らしに小さな幸せを</h2>
      <input
       type="text" 
       value={inputWord}
       onChange={ (e) => setInputWord(e.target.value)}
       placeholder='文字を入力'
      />
      <h2>{inputWord}</h2>
      <TipsBoard></TipsBoard>
    </>
  )
}

export default App

import { useState, memo } from "react";
import { CircleX } from 'lucide-react';



const PostTip = memo(({isPop, setIsPop}) => {
    const [inputTitle, setInputTitle] = useState("");
    const [inputExplanation, setExplanation] = useState("");

    const SubmitTip = async (e) => {
        //投稿する処理
        e.preventDefault();
  
        const postData = {
            tipTitle: inputTitle,       // stateから取得
            tipExplanation: inputExplanation,  // stateから取得
        };

        try {
            //const response = await fetch("http://localhost:8000/tips", {
            const response = await fetch(`${import.meta.env.VITE_API_URL}/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(postData), // 2項目だけ送る
            });
            
            if (response.ok) {
            // 成功時の処理（一覧の再取得など）
            }
        } catch (error) {
            console.error("Error:", error);
        }
        //入力内容をリセット
        setInputTitle("");
        setExplanation("");
    }

    return(
        <div className={`postArea ${isPop ? "isPop" : ""}`}>
        <div className="tip postTip">
            <a className="tipDetails" aria-label="詳細を見る" />
            <form action="" onSubmit={SubmitTip}>
                <input
                className="postTipInput postTipInputTitle"
                type="text" 
                value={inputTitle}
                onChange={ (e) => setInputTitle(e.target.value)}
                placeholder='タイトルを入力'
                />
                <input
                className="postTipInput postTipInputExplanation"
                type="text" 
                value={inputExplanation}
                onChange={ (e) => setExplanation(e.target.value)}
                placeholder='説明を入力'
                />
                <button type="submit" className="postButton">投稿する</button>
            </form>
            
            <div className="tipFooter">
                <span className="tipLike">
                    <span className="tipHeart" aria-hidden="true">👍</span>
                    〇
                </span>
            </div>
        </div>
        
        <button className="closeButton" onClick={()=>setIsPop(false)}>
            <CircleX
            size={50}        // サイズ
            color="#ffffff"    // 色
            strokeWidth={2}  // 線の太さ
            />
        </button>
        </div>
        
    );
})

export default PostTip;
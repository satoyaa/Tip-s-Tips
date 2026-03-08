import { useState, memo } from "react";

const PostTip = memo(({isPop, setIsPop}) => {
    const [inputTitle, setInputTitle] = useState("");
    const [inputExplanation, setExplanation] = useState("");
    const changeLikes = () => {
        if(isClicked){
            setTipLike((perv) => perv - 1);
        }else{
            setTipLike((perv) => perv + 1);
        }
        setIsClicked(!isClicked);
    }

    const clickPostTip = () => {
        //投稿する処理

        //入力内容をリセット
        setInputTitle("");
        setExplanation("");
    }
    return(
        <div className={`postArea ${isPop ? "isPop" : ""}`}>
        <div className="tip postTip">
            <a className="tipDetails" aria-label="詳細を見る" />
            <h2 className="tipTitle">
                <input
                className="postTipInput postTipInputTitle"
                type="text" 
                value={inputTitle}
                onChange={ (e) => setInputTitle(e.target.value)}
                placeholder='タイトルを入力'
                />
            </h2>
            <p className="tipText">
                <input
                className="postTipInput postTipInputExplanation"
                type="text" 
                value={inputExplanation}
                onChange={ (e) => setExplanation(e.target.value)}
                placeholder='説明を入力'
                />
            </p>
            <div className="tipFooter">
                <span className="tipLike">
                    <span className="tipHeart" aria-hidden="true">👍</span>
                    〇
                </span>
            </div>
        </div>
        <button className="postButton" onClick={clickPostTip}>投稿する</button>
        <button className="postButton" onClick={()=>setIsPop(false)}>閉じる</button>
        </div>
        
    );
})

export default PostTip;
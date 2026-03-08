import { useState } from "react";

const Tip = ({tipTitle, tipExplanation, tipLikes, tipDetails, top, left, rotate}) => {
    const [tipLike, setTipLike] = useState(tipLikes);
    const [isClicked, setIsClicked] = useState(false);
    const changeLikes = () => {
        if(isClicked){
            setTipLike((perv) => perv - 1);
        }else{
            setTipLike((perv) => perv + 1);
        }
        setIsClicked(!isClicked);
    }

    return(
        <div className="tip" style={{top:`${top}px`, left:`${left}px`, transform: `rotate(${rotate}deg)`}}>
            <a href={tipDetails} className="tipDetails" aria-label="詳細を見る" />
            <h2 className="tipTitle">{tipTitle}</h2>
            <p className="tipText">{tipExplanation}</p>
            <div className="tipFooter">
                <span className="tipLike">
                    <span className="tipHeart" aria-hidden="true" onClick={() => changeLikes()}>👍</span>
                    {tipLike}
                </span>
            </div>
        </div>
    );
}

export default Tip;
import { useState } from "react";

const Tip = ({tipTitle, tipExplanation, tipLikes, tipDetails, top, left}) => {
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
        <div className="tip card" style={{top:`${top}px`, left:`${left}px`}}>
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
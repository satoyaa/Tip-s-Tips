import { useEffect, useState, useContext } from "react";

const Tip = ({data, setTips}) => {
    const [tipLike, setTipLike] = useState(data.tipLikes);
    const [isClicked, setIsClicked] = useState(false);

    // propsのtipLikesが変わったらローカル状態に反映
    useEffect(() => {
        setTipLike(data.tipLikes);
    }, [data.tipLikes]);

    const changeLikes = () => {
        const nextLike = isClicked ? tipLike - 1 : tipLike + 1;
        setTipLike(nextLike);

        // 親のtips配列も更新しておく
        setTips((prevTips) =>
            prevTips.map((tip) =>
                tip.id === data.id ? { ...tip, tipLikes: nextLike } : tip
            )
        );

        setIsClicked(!isClicked);
        console.log(isClicked);
    }

    return(
        <div className="tip" style={{top:`${data.tipTop}px`, left:`${data.tipLeft}px`, transform: `rotate(${data.tipRotate}deg)`}}>
            <a href={data.tipDetails} className="tipDetails" aria-label="詳細を見る" />
            <h2 className="tipTitle">{data.tipTitle}</h2>
            <p className="tipText">{data.tipExplanation}</p>
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
import { useEffect, useState } from "react";

const Tip = ({ data, setTips }) => {
  const [tipLike, setTipLike] = useState(data.tipLikes);
  const [isClicked, setIsClicked] = useState(false);

  // propsのtipLikesが変わったらローカル状態に反映
  useEffect(() => {
    setTipLike(data.tipLikes);
  }, [data.tipLikes]);

  const changeLikes = async () => {
    const previousLike = tipLike;
    const previousClicked = isClicked;
    const nextLike = isClicked ? tipLike - 1 : tipLike + 1;

    // 先にUIを更新して、API が遅い場合にもレスポンスを良くする
    setTipLike(nextLike);
    setIsClicked(!isClicked);
    setTips((prevTips) =>
      prevTips.map((tip) =>
        tip.id === data.id ? { ...tip, tipLikes: nextLike } : tip
      )
    );

    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_URL}/tips/${data.id}/likes`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tipLikes: nextLike }),
        }
      );
      if (!res.ok) {
        throw new Error("Failed to update like");
      }
    } catch (error) {
      console.error("Failed to persist like:", error);
      // 失敗したら元に戻す
      setTipLike(previousLike);
      setIsClicked(previousClicked);
      setTips((prevTips) =>
        prevTips.map((tip) =>
          tip.id === data.id ? { ...tip, tipLikes: previousLike } : tip
        )
      );
    }
  };

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
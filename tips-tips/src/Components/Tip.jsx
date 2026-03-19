import { useEffect, useState } from "react";

const Tip = ({ data, setTips, layout }) => {
    const [tipLike, setTipLike] = useState(data.tipLikes);
    const [isClicked, setIsClicked] = useState(false);

    // propsのtipLikesが変わったらローカル状態に反映
    useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTipLike(data.tipLikes);
  }, [data.tipLikes]);

    const changeLikes = () => {
        const nextLike = isClicked ? tipLike - 1 : tipLike + 1;
        console.log("[Tip] changeLikes called", { id: data.id, nextLike });

        setTipLike(nextLike);

        // 親のtips配列も更新しておく
        setTips((prevTips) =>
            prevTips.map((tip) =>
                tip.id === data.id ? { ...tip, tipLikes: nextLike } : tip
            )
        );

        setIsClicked(!isClicked);

        const url = `${import.meta.env.VITE_API_URL}/tips/${data.id}/likes`;
        console.log("[Tip] sending PATCH", { url, body: { tipLikes: nextLike } });

        fetch(url, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tipLikes: nextLike }),
        })
          .then((res) => {
            if (!res.ok) {
              throw new Error(`HTTP ${res.status}`);
            }
            return res.json();
          })
          .then((json) => {
            console.log("[Tip] PATCH response", json);
          })
          .catch((error) => {
            console.error("[Tip] Failed to persist like:", error);
            // 失敗したら元に戻す
            setTipLike(tipLike);
            setIsClicked(isClicked);
            setTips((prevTips) =>
              prevTips.map((tip) =>
                tip.id === data.id ? { ...tip, tipLikes: tipLike } : tip
              )
            );
          });
    }

    return(
        <div
      className="tip"
      style={
        layout === "grid"
          ? {}
          : { top: `${data.tipTop}px`, left: `${data.tipLeft}px`, transform: `rotate(${data.tipRotate}deg)` }
      }
    >
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
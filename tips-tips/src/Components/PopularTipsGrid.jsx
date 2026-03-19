import { useEffect, useState } from "react";
import TipsBoard from "./TipsBoard";

export default function PopularTipsGrid() {
  const [tips, setTips] = useState([]);

  useEffect(() => {
    const fetchPopular = async () => {
      try {
        const url = new URL(`${import.meta.env.VITE_API_URL}/tips`);
        url.searchParams.append("sort", "likes");
        url.searchParams.append("order", "desc");

        const res = await fetch(url);
        const data = await res.json();

        // 先頭50件のみ表示
        setTips(data.slice(0, 50));
      } catch (e) {
        console.error("PopularTipsGrid fetch failed", e);
      }
    };

    fetchPopular();
  }, []);

  return (
    <TipsBoard
      isDisplay={true}
      tips={tips}
      setTips={setTips}
      layout="grid"
    />
  );
}

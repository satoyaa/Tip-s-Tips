import { useEffect, useState } from "react";
import TipsBoard from "./TipsBoard";
import { Swiper, SwiperSlide } from 'swiper/react';
import { Navigation, Pagination } from 'swiper/modules';
import Tip from './Tip'

import 'swiper/css';
import 'swiper/css/navigation';
import 'swiper/css/pagination';


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
    <>
    <h2>あなたへのおすすめ</h2>
      <div className="swiperContainer">
        <Swiper
          modules={[Navigation, Pagination]}
          navigation
          pagination={{ clickable: true }}
          centeredSlides={true}
          spaceBetween={30}
          slidesPerView={"auto"}
          breakpoints={{
            600: {slidesPerView:2 },
            900: { slidesPerView: 3 },
            1028: { slidesPerView: 4 }
          }}
        >
          {tips.map((data) => {
            return (
              <SwiperSlide key={data.id}>
                <Tip
                  data={data}
                  setTips={setTips}
                  layout={"grid"}
                />
              </SwiperSlide>
            )
          })}
        </Swiper>
      </div>
    </>
  );
}

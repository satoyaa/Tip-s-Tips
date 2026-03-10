import demoData from '../Data/DemoData'
import Tip from './Tip'
import { memo } from 'react';


const TipsBoard = memo(({isDisplay, recipes}) => {
    // APIのTipsデータがあればそちらを表示、なければデモデータ
    const hasApiData = recipes && recipes.length > 0;
    const displayData = hasApiData ? recipes : demoData;

    return (
        <div className={`tipsBoard ${isDisplay ? "isDisplay" : ""}`}>
            {displayData.map((data, index) => {
                const left = (index * 400) % 1200;
                const top = Math.floor(index / 3) * 300;
                const rotate = (Math.random()-0.5)*10;

                return (
                <Tip key={data.id}
                 tipTitle={data.tipTitle} 
                 tipExplanation={data.tipExplanation}
                 tipLikes={data.tipLikes ?? 0} 
                 tipDetails={data.source[0]}
                 top={top}
                 left={left}
                 rotate={rotate}
                 >
                </Tip>
                );
            })}
        </div>
    );
});

export default TipsBoard;
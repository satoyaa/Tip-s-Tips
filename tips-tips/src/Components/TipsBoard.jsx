import Tip from './Tip'
import { memo } from 'react';


const TipsBoard = memo(({ isDisplay, tips = [], setTips, layout }) => {
    const boardHeight = tips?.[0]?.tipsBoardHeight ?? 500;
    console.log(boardHeight);

    return (
        <div
            className={`tipsBoard ${isDisplay ? "isDisplay" : ""} ${layout}`}
            style={{ height: `${boardHeight}px` }}
        >
            {tips.map((data) => {
                return (
                    <Tip
                        key={data.id}
                        data={data}
                        setTips={setTips}
                        layout={layout}
                    />
                );
            })}
        </div>
    );
});

export default TipsBoard;
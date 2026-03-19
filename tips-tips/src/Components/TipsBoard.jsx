import Tip from './Tip'
import { memo } from 'react';


const TipsBoard = memo(({ isDisplay, tips, setTips, layout }) => {
    return (
        <div className={`tipsBoard ${isDisplay ? "isDisplay" : ""} ${layout}`}>
            {tips.map((data) => {
                return (
                <Tip key={data.id} 
                data={data}
                setTips={setTips}
                layout={layout}
                 >
                </Tip>
                );
            })}
        </div>
    );
});

export default TipsBoard;
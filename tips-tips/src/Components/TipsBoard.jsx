import Tip from './Tip'
import { memo } from 'react';


const TipsBoard = memo(({isDisplay, tips, setTips}) => {
    return (
        <div className={`tipsBoard ${isDisplay ? "isDisplay" : ""}`}>
            {tips.map((data) => {
                return (
                <Tip key={data.id} 
                data={data}
                setTips={setTips}
                 >
                </Tip>
                );
            })}
        </div>
    );
});

export default TipsBoard;
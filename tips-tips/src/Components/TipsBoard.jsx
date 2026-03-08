import demoData from '../Data/DemoData'
import Tip from './Tip'


const TipsBoard = () => {

    return (
        <div className='tipsBoard'>
            {demoData.map((data, index) => {
                const left = (index * 400) % 1200;
                const top = Math.floor(index / 3) * 300;

                return (
                <Tip id={data.id}
                 tipTitle={data.tipTitle} 
                 tipExplanation={data.tipExplanation}
                 tipLikes={data.tipLikes} 
                 tipDetails={data.source[0]}
                 top={top}
                 left={left}
                 >
                </Tip>
                );
            })}
        </div>
    );
}

export default TipsBoard;
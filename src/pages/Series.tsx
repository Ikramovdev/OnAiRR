import  { useEffect, useState } from 'react'
import Header from '../components/Header'
import Footer from '../components/Footer'
import Instance from '../hook/Instance'
import { API_KEY } from '../hook/useEnv'
import type { MovieType } from './Movies'
import { useNavigate } from 'react-router-dom'
import { PATH } from '../hook/usePath'

const Series = () => {
  const [seriesData, setSeriesData] = useState<MovieType[]>([])
  const navigate = useNavigate()
  useEffect(() => {
    Instance.get(`3/trending/movie/day?language=en-US`, {
      headers: {
        Accept: 'application/json',
        Authorization: `Bearer ${API_KEY}`
      }
    }).then(res => {
      setSeriesData(res.data.results);
    })
  }, [])
  return (
    <div>
      <Header />
      <div className='MovieBody'>
        <div className='max-w-[1400px] mx-auto py-20'>
          <h3 className='font-regular text-[24px] lg:text-[32px] text-white mb-[32px]'>Recommended Series</h3>
          <div className='overflow-x-auto'>
            <div className='overflow-x-auto py-4'>
              <div className='flex items-center gap-5 lg:gap-6 w-max lg:px-4'>
                {seriesData?.map((item: MovieType) => (
                  <div onClick={() => navigate(`${PATH.channels}/${item.id}`)} key={item.id} className='w-[300px] h-[400px] cursor-pointer border-[2px] rounded-[20px] overflow-hidden group relative duration-300 border-white transform-gpu hover:scale-[1.05] hover:z-30' >
                    <img src={`https://image.tmdb.org/t/p/w500${item.backdrop_path}`} alt={item.title} className="w-full h-full object-cover" />
                    <div className="absolute bottom-[-100%] group-hover:bottom-0 text-center flex flex-col items-center justify-center text-white z-20 p-4 duration-300 bg-[#00000099] h-full w-full">
                      <h4 className='font-bold text-lg mb-2 line-clamp-3'>{item.title}</h4>
                      <p className='text-sm mb-10 line-clamp-4'>{item.overview?.substring(0, 100)}...</p>
                      <button type='submit' className='mt-5 px-4 py-2 bg-red-500 text-white hover:opacity-75 cursor-pointer rounded-md'>Watch Now</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}

export default Series

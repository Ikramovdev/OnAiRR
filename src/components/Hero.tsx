import InceptionBG from "../assets/images/Inception.jpg"
import MoviesBg from "../assets/images/MoviesBG.jpg"
import Avatar from "../assets/images/Avatar.jpg"
import Interstellar from "../assets/images/Interstellar.jpg"
import Matrix from "../assets/images/Matrix.jpg"
import { Swiper, SwiperSlide } from 'swiper/react';
import { Autoplay, Pagination, Navigation } from 'swiper/modules';
import 'swiper/css';
import 'swiper/css/pagination';
import 'swiper/css/navigation';

interface CaruselProductType {
  id: number,
  title: string,
  series: number,
  episode: number,
  discription: string
  image: string
}

const Hero = () => {
  const HeroCaruselProduct: CaruselProductType[] = [
    {
      id: 1,
      title: 'Inception',
      series: 4,
      episode: 12,
      discription: "Cobb steals information from his targets by entering their dreams. Saito offers to wipe clean Cobb's criminal history as payment for performing an inception on his sick competitor's son.",
      image: InceptionBG
    },
    {
      id: 2,
      title: 'Avatar',
      series: 3,
      episode: 10,
      discription: "A paraplegic Marine dispatched to the moon Pandora on a unique mission becomes torn between following his orders and protecting the world he feels is his home.",
      image: Avatar
    },
    {
      id: 3,
      title: 'Interstellar',
      series: 1,
      episode: 8,
      discription: "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.",
      image: Interstellar
    },
    {
      id: 4,
      title: 'The Matrix',
      series: 4,
      episode: 15,
      discription: "A computer programmer discovers that reality as he knows it is a simulation created by machines, and joins a rebellion to break free from the system.",
      image: Matrix
    },
    {
      id: 5,
      title: 'All',
      series: 4,
      episode: 15,
      discription: "Dive into a universe of un-ending content and channels",
      image: MoviesBg
    },
  ]

  return (
    <section className='hero relative w-full h-screen'>
      <Swiper spaceBetween={0} slidesPerView={1} loop={true} effect={"fade"} centeredSlides={true} autoplay={{ delay: 3000, disableOnInteraction: false, }} pagination={{ clickable: true, dynamicBullets: true }} navigation={true} modules={[Autoplay, Pagination, Navigation]} className="mySwiper h-full">
        {HeroCaruselProduct?.map(item => (
          <SwiperSlide key={item.id} className='relative w-full h-full'>
            <img src={item.image} alt={item.title} className='w-full h-full object-cover'/>
            <div className='absolute bottom-[20%] left-[5%] text-white z-10 max-w-[600px]'>
              <h1 className='text-5xl font-bold mb-4'>{item.title}</h1>
              <div className='flex gap-4 mb-4'>
                <span>{item.series} Series</span>
                <span>{item.episode} Episodes</span>
              </div>
              <p className='text-lg'>{item.discription}</p>
              <button className='mt-6 bg-red-600 hover:bg-red-700 px-8 py-3 rounded-full font-semibold'>
                Watch Now
              </button>
            </div>
            <div className='absolute inset-0 bg-gradient-to-t from-black/70 to-transparent'></div>
          </SwiperSlide>
        ))}
      </Swiper>
    </section>
  )
}

export default Hero

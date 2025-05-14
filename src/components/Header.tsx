import { useEffect, useState, type FormEvent } from 'react'
import { MenuIcon, SearchIcon, SiteLogo, UserIcon } from '../assets/Icon'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { PATH } from '../hook/usePath'
import Modal from '@mui/material/Modal';
import siteLogo from "../assets/images/siteLogo.svg"
import toast, { Toaster } from 'react-hot-toast';
import CloseIcon from '@mui/icons-material/Close';
import useDebounce from '../hook/useDebaunce';
import Instance from '../hook/Instance';
import { API_KEY } from '../hook/useEnv';
import type { MovieType } from '../pages/Movies';


interface NavbarType {
  id: number,
  title: string,
  path: string
}
interface dataType {
  password: string,
  email: string
}

const Header = () => {
  const [showModal, setSHowModal] = useState<boolean>(false)
  const [menu, setMenu] = useState<boolean>(false)
  const [userName, setUserName] = useState<string | null>(null);
  const [mobileModal, setMobileModal] = useState<boolean>(false)
  const [query, setQuery] = useState<string>('');
  const debouncedQuery = useDebounce(query, 500);
  const [searchData, SearchData] = useState<MovieType[]>([])
  const location = useLocation();

  const NavbarList: NavbarType[] = [
    {
      id: 1,
      title: 'Movies',
      path: PATH.movies
    },
    {
      id: 2,
      title: 'Series',
      path: PATH.series
    },
    {
      id: 3,
      title: 'Channels',
      path: PATH.channels
    },
    {
      id: 4,
      title: 'Music',
      path: PATH.music
    }
  ]
  // useEffect(() =>{
  //   setUserName(localStorage.getItem('user'));
  // },[])
  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const target = e.target as HTMLFormElement;
    const data: dataType = {
      password: target.password.value,
      email: target.email.value
    };
    localStorage.setItem('user', data.email);
    setUserName(data.email);
    setTimeout(() => {
      setSHowModal(false);
      setMobileModal(false)
      setMenu(false)
      toast.success('Successfully signed in!')
    }, 200);
    target.email.value = "";
    target.password.value = "";
  }
  function handleSearchChange(e: React.ChangeEvent<HTMLInputElement>) {
    setQuery(e.target.value);
    console.log(e.target.value);

  }
  useEffect(() => {
    if (debouncedQuery) {
      console.log('Search:', debouncedQuery);
      Instance.get(`/3/search/movie?include_adult=false&language=en-US&page=1`, {
        headers: {
          Authorization: `Bearer ${API_KEY}`,
          accept: `application/json`
        }
      }).then(res => {
        SearchData(res.data.results);
      })
    }
  }, [debouncedQuery]);
  const resulText: MovieType[] | string = searchData[0] ? searchData : 'No Results'
  useEffect(() => {
    if (resulText == 'No Results') {
      console.log("This didn't work.")
    }
  }, [])
  return (
    <>
      {/* Desktop Responsive */}
      <div className={`hidden lg:block w-full ${location.pathname.startsWith(PATH.channels) ? 'bg-[#00000099]' : 'bg-[#212121]'} z-50 relative`}>
        <Toaster position="top-center" reverseOrder={false} />
        <div className='max-w-[1400px] mx-auto py-7 flex justify-between'>
          <div className='flex items-center gap-[56px]'>
            <Link className='flex items-center gap-2' to={`/`}>
              <SiteLogo />
            </Link>
            <ul className='flex items-center gap-10'>
              {NavbarList.map((item: NavbarType) => (
                <li key={item.id}>
                  <NavLink className='px-[20px] py-[10px] font-medium text-white text-[24px] duration-200' to={item.path}>
                    {item.title}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
          <div className='flex items-center gap-5'>
            <label className='w-[334px] py-3 cursor-pointer bg-black rounded-[8px] flex gap-2 pl-5 pr-1'>
              <div className=' '><SearchIcon /></div>
              <input onChange={handleSearchChange} className='text-white w-full outline-none' type="text" placeholder='Search' />
            </label>
            <button onClick={() => setSHowModal(true)} className='text-white flex gap-2 cursor-pointer'>
              <UserIcon />
              <span>{userName != null ? userName : 'Profile'}</span>
            </button>
          </div>
        </div>
      </div>
      <Modal open={showModal} onClose={() => setSHowModal(false)} aria-labelledby="login-modal" aria-describedby="login-form">
        <div className='hidden lg:block absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full max-w-md' >
          <img className='mx-auto mb-10' src={siteLogo} alt="siteLogo" width={100} height={100} />
          <div className="modal bg-[black] rounded-lg p-8 shadow-lg text-white">
            <h1 className="text-lg font-medium mb-6 text-center" id="login-modal">Login to get started</h1>
            <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4" id="login-form">
              <label>
                <input type="text" name="email" required placeholder="Please enter Mobile/Email address" className="w-full px-4 py-3 rounded-md bg-white/10 text-white text-sm outline-none focus:bg-white/20 placeholder:text-white/50 transition" />
              </label>
              <label>
                <input type="password" name="password" required placeholder="password" className="w-full px-4 py-3 rounded-md bg-white/10 text-white text-sm outline-none focus:bg-white/20 placeholder:text-white/50 transition" />
              </label>
              <button type="submit" className="cursor-pointer w-full max-w-[150px] mx-auto mt-5 py-2 bg-[#e94362] hover:bg-[#d13353] text-white rounded-full font-medium transition block" > Sign in </button>
            </form>
            <div className="mt-3 text-center">
              <a href="#" className="text-white/60 hover:text-white/80 text-sm transition">Forgot password?</a>
            </div>
            <div className="mt-6 text-center">
              <button onClick={() => setSHowModal(false)} className="text-white text-sm hover:opacity-80 transition cursor-pointer">Back to website</button>
            </div>
          </div>
        </div>
      </Modal>
      {/* Desktop Responsive */}

      {/* Mobile Responsive */}
      <div className={`block lg:hidden w-full ${location.pathname.startsWith(PATH.channels) ? 'bg-[#00000099]' : 'bg-[#212121]'} z-50 relative`}>
        <Toaster position="top-center" reverseOrder={false} />
        <div className='max-w-full mx-5 py-5 flex justify-between'>
          <Link className='cursor-pointer' to={`/`}>
            <img src={siteLogo} alt="siteLogo" width={80} height={80} />
          </Link>
          {menu ? null :
            <button onClick={() => setMenu(true)}>
              <MenuIcon />
              <p className='font-regular text-[15px] text-white'>Menu</p>
            </button>}
        </div>
      </div>
      {mobileModal ?
        <Modal open={mobileModal} onClose={() => setMobileModal(false)}>
          <div className='backdrop-blur-[68px] pt-10 px-5 block lg:hidden'>
            <img className='mx-auto mb-10' src={siteLogo} alt="siteLogo" width={100} height={100} />
            <div className="modal bg-[black] rounded-lg p-8 shadow-lg text-white">
              <h1 className="text-lg font-medium mb-6 text-center" id="login-modal">Login to get started</h1>
              <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4" id="login-form">
                <label>
                  <input type="text" name="email" required placeholder="Please enter Mobile/Email address" className="w-full px-4 py-3 rounded-md bg-white/10 text-white text-sm outline-none focus:bg-white/20 placeholder:text-white/50 transition" />
                </label>
                <label>
                  <input type="password" name="password" required placeholder="password" className="w-full px-4 py-3 rounded-md bg-white/10 text-white text-sm outline-none focus:bg-white/20 placeholder:text-white/50 transition" />
                </label>
                <button type="submit" className="cursor-pointer w-full max-w-[150px] mx-auto mt-5 py-2 bg-[#e94362] hover:bg-[#d13353] text-white rounded-full font-medium transition block" > Sign in </button>
              </form>
              <div className="mt-3 text-center">
                <a href="#" className="text-white/60 hover:text-white/80 text-sm transition">Forgot password?</a>
              </div>
              <div className="mt-6 text-center">
                <button onClick={() => setMobileModal(false)} className="text-white text-sm hover:opacity-80 transition cursor-pointer">Back to website</button>
              </div>
            </div>
          </div>
        </Modal> :
        <Modal open={menu} onClose={() => setMenu(false)}>
          <div className='w-full h-screen px-5 pt-10 backdrop-blur-[68px] block lg:hidden'>
            <div className='flex mb-3 justify-between'>
              <Link className='cursor-pointer' to={`/`}>
                <img src={siteLogo} alt="siteLogo" width={80} height={80} />
              </Link>
              <button onClick={() => setMenu(false)} className='text-white'>
                <CloseIcon className='scale-[1.7]' fontSize='large' />
                <p className='font-regular text-[15px] text-white'>Menu</p>
              </button>
            </div>
            <label className='w-[334px] mx-auto py-3 cursor-pointer bg-black rounded-[8px] flex gap-2 pl-5 pr-1'>
              <div className=' '><SearchIcon /></div>
              <input className='text-white w-full outline-none' type="text" placeholder='Search' />
            </label>
            <ul className='mt-10 flex text-start flex-col gap-10'>
              {NavbarList.map((item: NavbarType) => (
                <li key={item.id}>
                  <NavLink className='px-[20px] py-[10px] font-medium text-white text-[24px] duration-200' to={item.path}>
                    {item.title}
                  </NavLink>
                </li>
              ))}
            </ul>
            <button onClick={() => setMobileModal(true)} className='text-white mt-7 flex gap-2 cursor-pointer'>
              <UserIcon />
              <span>{userName != null ? userName : 'Profile'}</span>
            </button>
          </div>
        </Modal>
      }
      {/* Mobile Responsive */}
    </>
  )
}

export default Header



// #212121
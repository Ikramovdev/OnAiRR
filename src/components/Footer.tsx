import { Link, useNavigate } from 'react-router-dom'
import SiteLogoFooter from "../assets/images/siteLogoFooter.svg"
import { AppleIcon, UserIcon } from '../assets/Icon'
import GooglePlayIcon from "../assets/images/GooglePlay.svg"
import FacebookIcon from '@mui/icons-material/Facebook'
import InstagramIcon from '@mui/icons-material/Instagram'
import TwitterIcon from '@mui/icons-material/Twitter';
import YouTubeIcon from '@mui/icons-material/YouTube';
import { Accordion, AccordionDetails, AccordionSummary, Typography } from '@mui/material'
import AddIcon from '@mui/icons-material/Add';
const Footer = () => {
    const navigate = useNavigate()
    function handleScrollTop() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    return (
        <footer className='bg-[#191919]'>
            <div className='hidden w-[1400px] mx-auto pt-15 pb-[32px] lg:flex justify-between'>
                <div className='w-[350px]'>
                    <Link onClick={handleScrollTop} to={`/`}>
                        <img src={SiteLogoFooter} alt='siteLogo' width={96} height={51} />
                    </Link>
                    <p className='font-regular text-[16px] text-[#8D8D8D] mt-[94px]'>Hot Africa, we offer original, exclusive and premium stories. Everything you want to watch, anytime, anywhere and as much.</p>
                    <ul className='flex items-center gap-5 mt-8'>
                        <li>
                            <button onClick={() => navigate(`https://www.apple.com/app-store/`)} className='w-[130px] apple  duration-300 cursor-pointer border-[2px] border-white rounded-[10px] flex items-center justify-between px-[10px] pt-[5px] pb-[4px]'>
                                <AppleIcon />
                                <div className='text-white flex flex-col'>
                                    <p className='text-[9px] text-center'>Dowland on the</p>
                                    <p className='text-[15px] text-center'>App Store</p>
                                </div>
                            </button>
                        </li>
                        <li>
                            <button onClick={() => navigate(`https://play.google.com/`)} className='w-[130px] googlePlay duration-300 cursor-pointer border-[2px] border-white rounded-[10px] flex items-center justify-between px-[10px] pt-[5px] pb-[4px]'>
                                <img className='w-[21px] h-[30px]' src={GooglePlayIcon} alt="GooglePlayIcon" width={21} height={30} />
                                <div className='text-white flex flex-col'>
                                    <p className='text-[9px] text-center'>Dowland on the</p>
                                    <p className='text-[15px] text-center'>App Store</p>
                                </div>
                            </button>
                        </li>
                    </ul>
                    <ul className='flex items-center gap-10 mt-8'>
                        <li className='w-[40px] h-[40px] group'>
                            <button onClick={() => navigate('https://www.facebook.com')} className='w-full h-full border-[1px] duration-300 border-[#363636] group-hover:border-[#55ACE3] rounded-full cursor-pointer'>
                                <span className='mx-auto'>
                                    <FacebookIcon className='!text-white !duration-300 group-hover:!text-[#55ACE3]' fontSize='small' />
                                </span>
                            </button>
                        </li>
                        <li className='w-[40px] h-[40px] group'>
                            <button onClick={() => navigate(`https://www.instagram.com`)} className='w-full h-full border-[1px] duration-300 border-[#363636] group-hover:border-[#55ACE3] rounded-full cursor-pointer'>
                                <span className='mx-auto'>
                                    <InstagramIcon className='!text-white !duration-300 group-hover:!text-[#55ACE3]' fontSize='small' />
                                </span>
                            </button>
                        </li>
                        <li className='w-[40px] h-[40px] group'>
                            <button onClick={() => navigate(`https://twitter.com`)} className='w-full h-full border-[1px] duration-300 border-[#363636] group-hover:border-[#55ACE3] rounded-full cursor-pointer'>
                                <span className='mx-auto'>
                                    <TwitterIcon className='!text-white !duration-300 group-hover:!text-[#55ACE3]' fontSize='small' />
                                </span>
                            </button>
                        </li>
                        <li className='w-[40px] h-[40px] group'>
                            <button onClick={() => navigate(`https://www.youtube.com/`)} className='w-full h-full border-[1px] duration-300 border-[#363636] group-hover:border-[#55ACE3] rounded-full cursor-pointer'>
                                <span className='mx-auto'>
                                    <YouTubeIcon className='!text-white !duration-300 group-hover:!text-[#55ACE3]' fontSize='small' />
                                </span>
                            </button>
                        </li>
                    </ul>
                    <div className='mt-[54px]'>
                        <p className='font-medium text-[16px] text-[#616161]'>Terms of use Privacy Policy SiteMap</p>
                        <p className='font-regular text-[16px] text-[#616161]'>Copyright © 2022 Hot Africa. All rights reserved.</p>
                    </div>
                </div>
                <div className='flex items-top gap-40'>
                    <div>
                        <strong className='font-bold text-white flex gap-2 mb-[22px]'>
                            <UserIcon />
                            Sign in
                        </strong>
                        <ul className='flex flex-col gap-4'>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>Personal data</p>
                            </li>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>Choosing a Plan</p>
                            </li>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>Payment</p>
                            </li>
                        </ul>
                    </div>
                    <div>
                        <strong className='font-bold text-white flex gap-2 mb-[22px]'>
                            Movies
                        </strong>
                        <ul className='flex flex-col gap-4'>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>Lock Upp</p>
                            </li>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>Pavitra Rishta</p>
                            </li>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>Girgit</p>
                            </li>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>Hai Taubba Season 3</p>
                            </li>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>Cartel</p>
                            </li>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>Crimes And Confessions</p>
                            </li>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>Puncch Beat Season 2</p>
                            </li>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>Broken But Beautiful Season 3</p>
                            </li>
                        </ul>
                    </div>
                    <div>
                        <strong className='font-bold text-white flex gap-2 mb-[22px]'>
                            Seriess
                        </strong>
                        <ul className='flex flex-col gap-4'>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>X.X.X. Season 2</p>
                            </li>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>Gandii Baat Season 5</p>
                            </li>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>Gandii Baat Season 6</p>
                            </li>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>Broken But Beautiful Season 1</p>
                            </li>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>Broken But Beautiful Season 2</p>
                            </li>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>Class Of 2020</p>
                            </li>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>Bekaaboo Season 1</p>
                            </li>
                            <li>
                                <p className='font-regular text-[18px] text-[#797979]'>Ragini MMS Returns Season 2</p>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
            <div className='max-w-[900px] mx-5 pt-15 pb-[32px] flex lg:hidden flex-col'>
                <div className="w-full bg-[#191919] py-4 mb-[58px]">
                    <Accordion className="!bg-[#191919] !text-white !border-b-[2px] !border-gray-800 !shadow-none">
                        <AccordionSummary
                            expandIcon={
                                <div className="w-6 h-6 border border-gray-600 rounded-full flex items-center justify-center text-white hover:border-[#55ACE3] hover:text-[#55ACE3] transition">
                                    <AddIcon fontSize="small" />
                                </div>
                            }
                        >
                            <Typography component="span" className="flex items-center gap-2">
                                <UserIcon />
                                Sign in
                            </Typography>
                        </AccordionSummary>
                        <AccordionDetails className="text-[#797979] text-[18px] flex flex-col gap-4">
                            <p>Personal data</p>
                            <p>Choosing a Plan</p>
                            <p>Payment</p>
                        </AccordionDetails>
                    </Accordion>
                    <Accordion className="!bg-[#191919] !text-white !border-b-[2px] !border-gray-800 !shadow-none">
                        <AccordionSummary
                            expandIcon={
                                <div className="w-6 h-6 border border-gray-600 rounded-full flex items-center justify-center text-white hover:border-[#55ACE3] hover:text-[#55ACE3] transition">
                                    <AddIcon fontSize="small" />
                                </div>
                            }
                        >
                            <Typography className="font-bold">Movies</Typography>
                        </AccordionSummary>
                        <AccordionDetails className="text-[#797979] text-[18px] flex flex-col gap-4">
                            <p>Lock Upp</p>
                            <p>Pavitra Rishta</p>
                            <p>Girgit</p>
                            <p>Hai Taubba Season 3</p>
                            <p>Cartel</p>
                            <p>Crimes And Confessions</p>
                            <p>Puncch Beat Season 2</p>
                            <p>Broken But Beautiful Season 3</p>
                        </AccordionDetails>
                    </Accordion>
                    <Accordion className="!bg-[#191919] !text-white !border-b-[2px] !border-gray-800 !shadow-none">
                        <AccordionSummary
                            expandIcon={
                                <div className="w-6 h-6 border border-gray-600 rounded-full flex items-center justify-center text-white hover:border-[#55ACE3] hover:text-[#55ACE3] transition">
                                    <AddIcon fontSize="small" />
                                </div>
                            }>
                            <Typography className="font-bold">Series</Typography>
                        </AccordionSummary>
                        <AccordionDetails className="text-[#797979] text-[18px] flex flex-col gap-4">
                            <p>X.X.X. Season 2</p>
                            <p>Gandii Baat Season 5</p>
                            <p>Gandii Baat Season 6</p>
                            <p>Broken But Beautiful Season 1</p>
                            <p>Broken But Beautiful Season 2</p>
                            <p>Class Of 2020</p>
                            <p>Bekaaboo Season 1</p>
                            <p>Ragini MMS Returns Season 2</p>
                        </AccordionDetails>
                    </Accordion>
                </div>
                <div className='w-[350px]'>
                    <Link onClick={handleScrollTop} to={`/`}>
                        <img className='mx-auto w-[170px] h-[91px]' src={SiteLogoFooter} alt='siteLogo' width={170} height={91} />
                    </Link>
                    <p className='font-regular text-center text-[16px] text-[#8D8D8D] mt-[43px]'>Hot Africa, we offer original, exclusive and premium stories. Everything you want to watch, anytime, anywhere and as much.</p>
                    <ul className='mx-auto flex items-center justify-center gap-5 mt-8'>
                        <li>
                            <button className='w-[130px] apple  duration-300 cursor-pointer border-[2px] border-white rounded-[10px] flex items-center justify-between px-[10px] pt-[5px] pb-[4px]'>
                                <AppleIcon />
                                <div className='text-white flex flex-col'>
                                    <p className='text-[9px] text-center'>Dowland on the</p>
                                    <p className='text-[15px] text-center'>App Store</p>
                                </div>
                            </button>
                        </li>
                        <li>
                            <button className='w-[130px] googlePlay duration-300 cursor-pointer border-[2px] border-white rounded-[10px] flex items-center justify-between px-[10px] pt-[5px] pb-[4px]'>
                                <img className='w-[21px] h-[30px]' src={GooglePlayIcon} alt="GooglePlayIcon" width={21} height={30} />
                                <div className='text-white flex flex-col'>
                                    <p className='text-[9px] text-center'>Dowland on the</p>
                                    <p className='text-[15px] text-center'>App Store</p>
                                </div>
                            </button>
                        </li>
                    </ul>
                    <ul className='mx-auto flex items-center justify-center gap-10 mt-8'>
                        <li className='w-[40px] h-[40px] group'>
                            <button className='w-full h-full border-[1px] duration-300 border-[#363636] group-hover:border-[#55ACE3] rounded-full cursor-pointer'>
                                <span className='mx-auto'>
                                    <FacebookIcon className='!text-white !duration-300 group-hover:!text-[#55ACE3]' fontSize='small' />
                                </span>
                            </button>
                        </li>
                        <li className='w-[40px] h-[40px] group'>
                            <button className='w-full h-full border-[1px] duration-300 border-[#363636] group-hover:border-[#55ACE3] rounded-full cursor-pointer'>
                                <span className='mx-auto'>
                                    <InstagramIcon className='!text-white !duration-300 group-hover:!text-[#55ACE3]' fontSize='small' />
                                </span>
                            </button>
                        </li>
                        <li className='w-[40px] h-[40px] group'>
                            <button className='w-full h-full border-[1px] duration-300 border-[#363636] group-hover:border-[#55ACE3] rounded-full cursor-pointer'>
                                <span className='mx-auto'>
                                    <TwitterIcon className='!text-white !duration-300 group-hover:!text-[#55ACE3]' fontSize='small' />
                                </span>
                            </button>
                        </li>
                        <li className='w-[40px] h-[40px] group'>
                            <button className='w-full h-full border-[1px] duration-300 border-[#363636] group-hover:border-[#55ACE3] rounded-full cursor-pointer'>
                                <span className='mx-auto'>
                                    <YouTubeIcon className='!text-white !duration-300 group-hover:!text-[#55ACE3]' fontSize='small' />
                                </span>
                            </button>
                        </li>
                    </ul>
                    <div className='mt-[54px] text-center'>
                        <p className='font-medium text-[16px] text-[#616161]'>Terms of use Privacy Policy SiteMap</p>
                        <p className='font-regular text-[16px] text-[#616161]'>Copyright © 2022 Hot Africa. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </footer>
    )
}

export default Footer

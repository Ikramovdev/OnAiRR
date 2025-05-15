import { Route, Routes } from 'react-router-dom'
import { PATH } from '../hook/usePath'
import Movies from '../pages/Movies'
import Series from '../pages/Series'
import Channels from '../pages/Channels'
import Music from '../pages/Music'  // Fixed import from your pages directory

const ShopRoutes = () => {
    return (
        <Routes>
            <Route element={<Movies />} path={PATH.movies} />
            <Route element={<Series />} path={PATH.series} />
            <Route element={<Channels />} path={PATH.channels} />
            <Route element={<Channels />} path={`${PATH.channels}/:id`} />
            <Route element={<Music />} path={PATH.music} />
        </Routes>
    )
}

export default ShopRoutes

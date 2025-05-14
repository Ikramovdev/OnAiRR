import { useEffect, useState } from "react"
import Header from "../components/Header"
import Footer from "../components/Footer"
import { useParams } from "react-router-dom"
import Instance from "../hook/Instance"
import { API_KEY } from "../hook/useEnv"
import { Film, Loader2, AlertCircle } from "lucide-react"

interface MovieDetails {
  title?: string
  backdrop_path?: string
  poster_path?: string
  overview?: string
  release_date?: string
}
interface Video {
  id: string;
  iso_639_1: string;
  iso_3166_1: string;
  key: string;
  name: string;
  site: string;
  size: number;
  type: string;
  official: boolean;
  published_at: string;
  updated_at: string;
}

const Channels = () => {
  const { id } = useParams()
  const [videoKey, setVideoKey] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [movieDetails, setMovieDetails] = useState<MovieDetails | null>(null)
  useEffect(() => {
    Instance.get(`3/movie/${id}?language=en-US`, {
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${API_KEY}`,
      },
    }).then((res) => {
      setMovieDetails(res.data)
    }).catch((err) => {
      console.error("Error fetching movie details:", err)
    })
    Instance.get(`3/movie/${id}/videos?language=en-US`, {
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${API_KEY}`,
      },
    }).then((res) => {
      console.log(res.data.results);
      const videos = res.data.results
      const trailer = videos.find(
        (video: Video) => video.site === "YouTube" && (video.type === "Trailer" || video.type === "Teaser"),
      )
      if (trailer) {
        setVideoKey(trailer.key)
      } else {
        setError("No trailer available for this movie")
      }
      setLoading(false)
    }).catch((err) => {
      console.error("Error:", err)
      setError("Failed to load trailer")
      setLoading(false)
    })
  }, [id])

  const backdropUrl = movieDetails?.backdrop_path ? `https://image.tmdb.org/t/p/original${movieDetails.backdrop_path}` : null
  const posterUrl = movieDetails?.poster_path ? `https://image.tmdb.org/t/p/w500${movieDetails.poster_path}` : null

  return (
    <div className="min-h-screen flex flex-col bg-gray-900 text-white">
      <Header />
      <main className="flex-1">
        {backdropUrl && (
          <div className="absolute top-0 left-0 w-full h-[100vh] z-0 opacity-20" style={{ backgroundImage: `url(${backdropUrl})`, backgroundSize: "cover", backgroundPosition: "center", backgroundRepeat: "no-repeat", }} />)}
        <div className="relative z-10 container mx-auto px-4 py-12">
          {movieDetails && (
            <div className="mb-8 flex flex-col md:flex-row gap-8">
              {posterUrl && (
                <div className="flex-shrink-0">
                  <img src={posterUrl || "/placeholder.svg"} alt={movieDetails.title || "Movie poster"} className="w-full md:w-64 rounded-lg shadow-lg" />
                </div>)}
              <div>
                <h1 className="text-3xl md:text-4xl font-bold mb-2">{movieDetails.title}</h1>
                {movieDetails.release_date && (
                  <p className="text-gray-400 mb-4">
                    Released: {new Date(movieDetails.release_date).toLocaleDateString()}
                  </p>)}
                <p className="text-gray-300 mb-6 max-w-2xl">{movieDetails.overview}</p>
              </div>
            </div>
          )}
          <div className="mt-8">
            <h2 className="text-2xl font-bold mb-6 flex items-center">
              <Film className="mr-2" /> Official Trailer
            </h2>
            <div className="bg-black/50 rounded-xl overflow-hidden shadow-2xl">
              {loading ? (
                <div className="flex items-center justify-center h-[450px]">
                  <Loader2 className="w-12 h-12 animate-spin text-gray-400" />
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center h-[450px] p-6 text-center">
                  <AlertCircle className="w-16 h-16 text-red-500 mb-4" />
                  <p className="text-xl font-medium text-gray-300">{error}</p>
                  <p className="text-gray-400 mt-2">Try checking another movie or come back later.</p>
                </div>
              ) : videoKey ? (
                <div className="aspect-video">
                  <iframe className="w-full h-full" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" src={`https://www.youtube.com/embed/${videoKey}?autoplay=0&rel=0&modestbranding=1`} title="Movie Trailer" allowFullScreen></iframe>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-[450px] p-6 text-center">
                  <AlertCircle className="w-16 h-16 text-yellow-500 mb-4" />
                  <p className="text-xl font-medium text-gray-300">No trailer found</p>
                  <p className="text-gray-400 mt-2">This movie doesn't have an official trailer yet.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  )
}

export default Channels

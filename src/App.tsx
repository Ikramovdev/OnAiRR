import './App.css'
import ShopRoutes from './routes/Index'


export interface Product {
  id: number;
  title: string;
  description: string;
  price: number;
  discountPercentage: number;
  rating: number;
  stock: number;
  brand: string;
  category: string;
  availabilityStatus: string;
  minimumOrderQuantity: number;
  shippingInformation: string;
  warrantyInformation: string;
  returnPolicy: string;
  sku: string;
  weight: number;
  thumbnail: string;
  images: string[];
  tags: string[];
  dimensions: {
    width: number;
    height: number;
    depth: number;
  };
  meta: {
    barcode: string;
    qrCode: string;
    createdAt: string;
    updatedAt: string;
  };
  reviews: {
    rating: number;
    comment: string;
    date: string;
    reviewerName: string;
    reviewerEmail: string;
  }[];
}

function App() {
  return <ShopRoutes />
}

export default App

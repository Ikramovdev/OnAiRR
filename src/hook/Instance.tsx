import axios, { type AxiosInstance } from "axios";
import { API_REQUEST } from "./useEnv";

const Instance: AxiosInstance = axios.create({
    baseURL: API_REQUEST,
});

export default Instance;

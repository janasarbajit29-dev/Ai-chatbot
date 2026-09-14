import { createBrowserRouter } from "react-router-dom";
import Workspace from "../pages/Workspace";
import Auth from "../pages/Auth";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Workspace />,
  },
  {
    path: "/auth",
    element: <Auth />,
  },
]);

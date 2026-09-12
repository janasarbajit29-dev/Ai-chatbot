import { createBrowserRouter } from "react-router-dom";
import Workspace from "../pages/Workspace";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Workspace />,
  },
]);

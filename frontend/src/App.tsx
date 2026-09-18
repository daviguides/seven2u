import { Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { ToastProvider } from "./components/Toast";
import { SearchPage } from "./features/search/SearchPage";
import { SeriesDetailPage } from "./features/series/SeriesDetailPage";

export default function App() {
  return (
    <ToastProvider>
      <Layout>
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/series/:seriesId" element={<SeriesDetailPage />} />
        </Routes>
      </Layout>
    </ToastProvider>
  );
}

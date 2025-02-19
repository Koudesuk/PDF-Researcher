import { pdfjs } from 'react-pdf';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

// Common PDF options
export const PDF_OPTIONS = {
  cMapUrl: 'https://unpkg.com/pdfjs-dist@3.11.174/cmaps/',
  cMapPacked: true,
  standardFontDataUrl: 'https://unpkg.com/pdfjs-dist@3.11.174/standard_fonts/',
};

// Calculate scale for zooming
export const calculateScale = (
  currentScale: number, 
  baseScale: number, 
  increment: boolean
): number => {
  const scaleDelta = baseScale * 0.1;
  const newScale = increment ? currentScale + scaleDelta : currentScale - scaleDelta;
  
  // Limit scale between 50% and 300% of base scale
  return Math.max(baseScale * 0.5, Math.min(baseScale * 3, newScale));
};
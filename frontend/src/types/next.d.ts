declare module 'next/types.js' {
  import type { Metadata, Viewport } from 'next';
  
  export type ResolvingMetadata = Promise<Metadata>;
  export type ResolvingViewport = Promise<Viewport>;
  export * from 'next/types';
}

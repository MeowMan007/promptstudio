export type RegionType =
  | 'header'
  | 'nav'
  | 'sidebar'
  | 'main'
  | 'footer'
  | 'modal'
  | 'overlay'
  | 'card'
  | 'form'
  | 'list'
  | 'custom';

export type ControlType =
  | 'button'
  | 'input'
  | 'checkbox'
  | 'radio'
  | 'select'
  | 'textarea'
  | 'image'
  | 'label'
  | 'link'
  | 'icon'
  | 'divider'
  | 'custom';

export type ControlState =
  | 'default'
  | 'hover'
  | 'active'
  | 'disabled'
  | 'error'
  | 'loading';

export type Breakpoint = 'mobile' | 'tablet' | 'desktop';

export interface ScreenRegion {
  id: string;
  label: string;
  x: number;
  y: number;
  width: number;
  height: number;
  region_type: RegionType;
}

export interface ScreenControl {
  id: string;
  region_id: string;
  control_type: ControlType;
  label: string;
  x: number;
  y: number;
  width: number;
  height: number;
  state?: ControlState;
}

export interface ScreenViewport {
  width: number;
  height: number;
  breakpoint: Breakpoint;
}

export interface ScreenPayload {
  regions: ScreenRegion[];
  controls: ScreenControl[];
  viewport: ScreenViewport;
  annotations?: string[];
}

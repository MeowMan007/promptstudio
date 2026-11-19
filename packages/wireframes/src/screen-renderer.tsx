import React from 'react';
import type { ScreenPayload, ScreenRegion, ScreenControl, ControlType } from './types';

// ── Control placeholder styles ───────────────────────────────────────────────

function controlStyle(type: ControlType, disabled: boolean): React.CSSProperties {
  const base: React.CSSProperties = {
    position: 'absolute',
    boxSizing: 'border-box',
    fontSize: 10,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    opacity: disabled ? 0.4 : 1,
  };

  switch (type) {
    case 'button':
      return {
        ...base,
        background: '#d0d8e8',
        border: '1.5px solid #7090b0',
        borderRadius: 4,
      };
    case 'input':
      return {
        ...base,
        background: '#fff',
        borderBottom: '2px solid #666',
        borderTop: 'none',
        borderLeft: 'none',
        borderRight: 'none',
        paddingLeft: 4,
        justifyContent: 'flex-start',
      };
    case 'textarea':
      return {
        ...base,
        background: '#fff',
        border: '1px solid #aaa',
        borderRadius: 2,
        padding: 4,
        alignItems: 'flex-start',
      };
    case 'checkbox':
      return {
        ...base,
        background: 'none',
        border: 'none',
        justifyContent: 'flex-start',
        gap: 4,
      };
    case 'radio':
      return {
        ...base,
        background: 'none',
        border: 'none',
        justifyContent: 'flex-start',
        gap: 4,
      };
    case 'select':
      return {
        ...base,
        background: '#fff',
        border: '1px solid #aaa',
        borderRadius: 2,
        paddingLeft: 4,
        justifyContent: 'space-between',
        paddingRight: 4,
      };
    case 'image':
      return {
        ...base,
        background: '#c8c8c8',
        border: '1px solid #999',
      };
    case 'label':
      return { ...base, background: 'none', border: 'none', fontWeight: 600 };
    case 'link':
      return {
        ...base,
        background: 'none',
        border: 'none',
        color: '#1a5cb0',
        textDecoration: 'underline',
      };
    case 'icon':
      return {
        ...base,
        background: 'none',
        border: '1px dashed #bbb',
        borderRadius: '50%',
        fontSize: 14,
      };
    case 'divider':
      return {
        ...base,
        background: 'none',
        border: 'none',
        borderTop: '1px solid #bbb',
      };
    default:
      return { ...base, background: '#eee', border: '1px dashed #aaa' };
  }
}

// ── Control placeholder content ──────────────────────────────────────────────

function ControlPlaceholder({ control, regionX, regionY }: {
  control: ScreenControl;
  regionX: number;
  regionY: number;
}) {
  const disabled = control.state === 'disabled';
  const style: React.CSSProperties = {
    ...controlStyle(control.control_type, disabled),
    left: control.x - regionX,
    top: control.y - regionY,
    width: control.width,
    height: control.height,
  };

  let inner: React.ReactNode = null;

  switch (control.control_type) {
    case 'image':
      // grey box with an X
      inner = (
        <svg width="100%" height="100%" viewBox="0 0 40 30" preserveAspectRatio="none">
          <line x1="0" y1="0" x2="40" y2="30" stroke="#999" strokeWidth="1" />
          <line x1="40" y1="0" x2="0" y2="30" stroke="#999" strokeWidth="1" />
        </svg>
      );
      break;
    case 'checkbox':
      inner = (
        <>
          <span style={{
            display: 'inline-block', width: 10, height: 10,
            border: '1.5px solid #555', borderRadius: 2, flexShrink: 0,
          }} />
          <span>{control.label}</span>
        </>
      );
      break;
    case 'radio':
      inner = (
        <>
          <span style={{
            display: 'inline-block', width: 10, height: 10,
            border: '1.5px solid #555', borderRadius: '50%', flexShrink: 0,
          }} />
          <span>{control.label}</span>
        </>
      );
      break;
    case 'select':
      inner = (
        <>
          <span>{control.label}</span>
          <span>▾</span>
        </>
      );
      break;
    case 'icon':
      inner = '◎';
      break;
    case 'divider':
      inner = null;
      break;
    default:
      inner = control.label || null;
  }

  return (
    <div
      style={style}
      title={`${control.control_type}: ${control.label}`}
      aria-label={`${control.control_type} ${control.label}`}
    >
      {inner}
    </div>
  );
}

// ── Region renderer ──────────────────────────────────────────────────────────

function RegionBlock({ region, controls }: {
  region: ScreenRegion;
  controls: ScreenControl[];
}) {
  const regionStyle: React.CSSProperties = {
    position: 'absolute',
    left: region.x,
    top: region.y,
    width: region.width,
    height: region.height,
    boxSizing: 'border-box',
    border: '1.5px dashed #9aabb5',
    background: '#f5f7f9',
    overflow: 'hidden',
  };

  const labelStyle: React.CSSProperties = {
    position: 'absolute',
    top: 2,
    left: 4,
    fontSize: 9,
    color: '#6b8090',
    fontFamily: 'sans-serif',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
    pointerEvents: 'none',
    whiteSpace: 'nowrap',
  };

  const myControls = controls.filter((c) => c.region_id === region.id);

  return (
    <div style={regionStyle} aria-label={`region: ${region.label}`}>
      <span style={labelStyle}>{region.label}</span>
      {myControls.map((control) => (
        <ControlPlaceholder
          key={control.id}
          control={control}
          regionX={region.x}
          regionY={region.y}
        />
      ))}
    </div>
  );
}

// ── Main ScreenRenderer component ────────────────────────────────────────────

export interface ScreenRendererProps {
  payload: ScreenPayload;
  /** Maximum rendered width in px. The canvas scales uniformly to fit. Default 800. */
  maxWidth?: number;
}

export function ScreenRenderer({ payload, maxWidth = 800 }: ScreenRendererProps) {
  const { viewport, regions, controls } = payload;
  const scale = Math.min(1, maxWidth / viewport.width);

  const outerStyle: React.CSSProperties = {
    width: viewport.width * scale,
    height: viewport.height * scale,
    overflow: 'hidden',
  };

  const innerStyle: React.CSSProperties = {
    position: 'relative',
    width: viewport.width,
    height: viewport.height,
    transformOrigin: 'top left',
    transform: `scale(${scale})`,
    background: '#ffffff',
    boxShadow: '0 0 0 1px #ccc',
    fontFamily: 'sans-serif',
  };

  return (
    <div
      style={outerStyle}
      role="img"
      aria-label={`Screen wireframe – ${viewport.breakpoint} ${viewport.width}×${viewport.height}`}
    >
      <div style={innerStyle}>
        {regions.map((region) => (
          <RegionBlock key={region.id} region={region} controls={controls} />
        ))}
      </div>
    </div>
  );
}

export default ScreenRenderer;

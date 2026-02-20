interface IconProps {
  size?: number;
  className?: string;
}

function SvgIcon({
  d,
  size = 14,
  className = '',
}: IconProps & { d: string | string[] }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {Array.isArray(d) ? (
        d.map((p, i) => <path key={i} d={p} />)
      ) : (
        <path d={d} />
      )}
    </svg>
  );
}

export const Music = (p: IconProps) => (
  <SvgIcon
    {...p}
    d={[
      'M9 18V5l12-2v13',
      'M9 18a3 3 0 1 1-6 0 3 3 0 0 1 6 0z',
      'M21 16a3 3 0 1 1-6 0 3 3 0 0 1 6 0z',
    ]}
  />
);
export const Upload = (p: IconProps) => (
  <SvgIcon
    {...p}
    d={[
      'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4',
      'M17 8l-5-5-5 5',
      'M12 3v12',
    ]}
  />
);
export const Download = (p: IconProps) => (
  <SvgIcon
    {...p}
    d={[
      'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4',
      'M7 10l5 5 5-5',
      'M12 15V3',
    ]}
  />
);
export const Sparkles = (p: IconProps) => (
  <SvgIcon
    {...p}
    d={[
      'M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z',
      'M18 14l1 3 3 1-3 1-1 3-1-3-3-1 3-1 1-3z',
    ]}
  />
);
export const Settings = (p: IconProps) => (
  <SvgIcon
    {...p}
    d={[
      'M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z',
      'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z',
    ]}
  />
);
export const ChevronDown = (p: IconProps) => (
  <SvgIcon {...p} d="M6 9l6 6 6-6" />
);
export const Help = (p: IconProps) => (
  <SvgIcon
    {...p}
    d={[
      'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z',
      'M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3',
      'M12 17h.01',
    ]}
  />
);
export const Loader = (p: IconProps) => (
  <SvgIcon
    {...p}
    d={['M21 12a9 9 0 1 1-6.219-8.56']}
    className={`${p.className || ''} animate-spin`}
  />
);
export const Check = (p: IconProps) => (
  <SvgIcon {...p} d="M20 6L9 17l-5-5" />
);
export const X = (p: IconProps) => (
  <SvgIcon {...p} d={['M18 6L6 18', 'M6 6l12 12']} />
);
export const Copy = (p: IconProps) => (
  <SvgIcon
    {...p}
    d={[
      'M20 9h-9a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2z',
      'M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1',
    ]}
  />
);
export const Code = (p: IconProps) => (
  <SvgIcon {...p} d={['M16 18l6-6-6-6', 'M8 6l-6 6 6 6']} />
);
export const FileMusic = (p: IconProps) => (
  <SvgIcon
    {...p}
    d={[
      'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z',
      'M14 2v6h6',
      'M10 16s.8-2 2-2 2 2 2 2-2',
      'M10 12v4',
    ]}
  />
);
export const BarChart = (p: IconProps) => (
  <SvgIcon {...p} d={['M18 20V10', 'M12 20V4', 'M6 20v-6']} />
);
export const GitCompare = (p: IconProps) => (
  <SvgIcon
    {...p}
    d={[
      'M18 21a2 2 0 1 0 0-4 2 2 0 0 0 0 4z',
      'M6 7a2 2 0 1 0 0-4 2 2 0 0 0 0 4z',
      'M6 7v8a2 2 0 0 0 2 2h2',
      'M18 17V9a2 2 0 0 0-2-2h-2',
    ]}
  />
);
export const List = (p: IconProps) => (
  <SvgIcon
    {...p}
    d={[
      'M8 6h13',
      'M8 12h13',
      'M8 18h13',
      'M3 6h.01',
      'M3 12h.01',
      'M3 18h.01',
    ]}
  />
);
export const Play = (p: IconProps) => (
  <SvgIcon {...p} d="M5 3l14 9-14 9V3z" />
);
export const Pause = (p: IconProps) => (
  <SvgIcon {...p} d={['M6 4h4v16H6z', 'M14 4h4v16h-4z']} />
);
export const Trash = (p: IconProps) => (
  <SvgIcon
    {...p}
    d={[
      'M3 6h18',
      'M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6',
      'M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2',
    ]}
  />
);
export const Clock = (p: IconProps) => (
  <SvgIcon
    {...p}
    d={[
      'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z',
      'M12 6v6l4 2',
    ]}
  />
);
export const ExternalLink = (p: IconProps) => (
  <SvgIcon
    {...p}
    d={[
      'M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6',
      'M15 3h6v6',
      'M10 14L21 3',
    ]}
  />
);

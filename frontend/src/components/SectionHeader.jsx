export function SectionHeader({ eyebrow, title, description }) {
  return (
    <div className="dashboardHeader">
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      {description && <p>{description}</p>}
    </div>
  );
}

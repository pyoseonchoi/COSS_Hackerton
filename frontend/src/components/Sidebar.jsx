import { Award, Calculator, MapPinned, Plane, SlidersHorizontal, Sprout } from 'lucide-react';

const navItems = [
  { id: 'income', label: '1. 소득 계산', icon: Calculator },
  { id: 'preferences', label: '2. 선호도 설정', icon: SlidersHorizontal },
  { id: 'candidates', label: '3. 농지 후보', icon: MapPinned },
  { id: 'drone', label: '4. 드론 분석', icon: Plane },
  { id: 'final', label: '5. 최종 추천', icon: Award }
];

export function Sidebar({ activeSection, onSectionChange }) {
  return (
    <aside className="sidebar">
      <div className="sidebarBrand">
        <span className="sidebarLogo">
          <Sprout size={30} />
        </span>
        <h1>청년농업 입지 진단</h1>
        <p>React Decision MVP</p>
      </div>

      <nav className="sidebarMenu" aria-label="대시보드 섹션">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              type="button"
              className={activeSection === item.id ? 'menuItem active' : 'menuItem'}
              onClick={() => onSectionChange(item.id)}
            >
              <Icon size={18} />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="sidebarFooter">
        <strong>해커톤 시연 가이드</strong>
        <span>소득 대체 계산과 원본 입지 진단 흐름을 하나의 React 대시보드로 통합했습니다.</span>
      </div>
    </aside>
  );
}

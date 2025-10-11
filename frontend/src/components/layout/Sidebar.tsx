import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Building2,
  Wallet,
  Tags,
  Settings as SettingsIcon,
  Receipt,
  CheckSquare,
  FileText,
  FolderOpen,
  Settings,
  LogOut,
  Grid3X3,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import { useAuth } from '../auth/AuthContext';

const Sidebar: React.FC = () => {
  const { logout } = useAuth();
  const [isBusinessExpanded, setIsBusinessExpanded] = useState(true);

  const mainNavItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  ];

  const businessNavItems = [
    { to: '/divisions', icon: Grid3X3, label: 'Project Divisions' },
    { to: '/accounts', icon: Wallet, label: 'Accounts' },
    { to: '/categories', icon: Tags, label: 'Categories' },
    { to: '/rules', icon: SettingsIcon, label: 'Rules' },
  ];

  const otherNavItems = [
    { to: '/expenses', icon: Receipt, label: 'Transactions' },
    { to: '/documents', icon: FolderOpen, label: 'Documents' },
    { to: '/approvals', icon: CheckSquare, label: 'Approvals' },
    { to: '/reports', icon: FileText, label: 'Reports' },
  ];

  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-primary-500 rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-xl">E</span>
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              exp<span className="text-primary-500">e</span>nsio
            </h1>
            <p className="text-xs text-gray-500">Expense Tracker</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {/* Main Navigation Items */}
        {mainNavItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-primary-50 text-primary-600'
                  : 'text-gray-700 hover:bg-gray-50'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}

        {/* Business Section */}
        <div className="space-y-1">
          <button
            onClick={() => setIsBusinessExpanded(!isBusinessExpanded)}
            className="flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors text-gray-700 hover:bg-gray-50 w-full text-left"
          >
            {isBusinessExpanded ? (
              <ChevronDown className="w-5 h-5" />
            ) : (
              <ChevronRight className="w-5 h-5" />
            )}
            <Building2 className="w-5 h-5" />
            <span className="font-medium">Business Setting</span>
          </button>

          {isBusinessExpanded && (
            <div className="ml-6 space-y-1">
              {businessNavItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center space-x-3 px-4 py-2 rounded-lg transition-colors text-sm ${
                      isActive
                        ? 'bg-primary-50 text-primary-600'
                        : 'text-gray-600 hover:bg-gray-50'
                    }`
                  }
                >
                  <item.icon className="w-4 h-4" />
                  <span className="font-medium">{item.label}</span>
                </NavLink>
              ))}
            </div>
          )}
        </div>

        {/* Other Navigation Items */}
        {otherNavItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-primary-50 text-primary-600'
                  : 'text-gray-700 hover:bg-gray-50'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Bottom Section */}
      <div className="p-4 border-t border-gray-200 space-y-1">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
              isActive
                ? 'bg-primary-50 text-primary-600'
                : 'text-gray-700 hover:bg-gray-50'
            }`
          }
        >
          <Settings className="w-5 h-5" />
          <span className="font-medium">Settings</span>
        </NavLink>
        <button
          onClick={logout}
          className="flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors text-red-600 hover:bg-red-50 w-full"
        >
          <LogOut className="w-5 h-5" />
          <span className="font-medium">Logout</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;

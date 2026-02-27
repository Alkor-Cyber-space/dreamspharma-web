
import {
  LayoutDashboard,
  Boxes,
  ShoppingCart,
  TrendingUp,
  CreditCard,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useState } from "react";

export default function Sidebar({ open, setOpen }) {
  const [inventoryOpen, setInventoryOpen] = useState(false);

  return (
    <>
      {/* Overlay */}
      {open && (
        <div
          onClick={() => setOpen(false)}
          className="fixed inset-0 bg-black/40 z-30 md:hidden"
        />
      )}

      <aside
        className={`
          fixed md:relative top-0 left-0 h-full 
          w-64 bg-gray-800 text-white p-6 z-40
          transition-transform duration-300
          ${open ? "translate-x-0" : "-translate-x-full"}
          md:translate-x-0 md:flex-shrink-0
        `}
      >
        <h1 className="text-2xl font-bold mb-10 tracking-wide">
          Banana ERP
        </h1>

        <nav className="space-y-2 text-sm">
          <SidebarItem
            to="/"
            icon={<LayoutDashboard size={18} />}
            name="Dashboard"
          />

          {/* Inventory with dropdown */}
          <div>
            <button
              onClick={() => setInventoryOpen(!inventoryOpen)}
              className="flex items-center justify-between w-full p-3 rounded-lg hover:bg-gray-700 transition"
            >
              <div className="flex items-center gap-3">
                <Boxes size={18} />
                <span>Inventory</span>
              </div>

              {inventoryOpen ? (
                <ChevronDown size={16} />
              ) : (
                <ChevronRight size={16} />
              )}
            </button>

            {/* Sublinks */}
            {inventoryOpen && (
              <div className="ml-8 mt-1 space-y-1">
                <SidebarSubItem 
                  to="/inventory/products" 
                  name="Products" />

                <SidebarSubItem
                  to="/inventory/stock"
                  name="Stock"
                />
                <SidebarSubItem
                  to="/inventory/add"
                  name="Add Stock"
                />
              </div>
            )}
          </div>

          <SidebarItem
            to="/sales/customers"
            icon={<TrendingUp size={18} />}
            name="Customers"
          />

          <SidebarItem
            to="/purchases/suppliers"
            icon={<ShoppingCart size={18} />}
            name="Suppliers"
          />

          <SidebarItem
            to="/expenses"
            icon={<CreditCard size={18} />}
            name="Expenses"
          />
        </nav>
      </aside>
    </>
  );
}

function SidebarItem({ icon, name, to }) {
  return (
    <Link
      to={to}
      className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-700 transition font-medium"
    >
      {icon}
      <span>{name}</span>
    </Link>
  );
}

function SidebarSubItem({ name, to }) {
  return (
    <Link
      to={to}
      className="block p-2 rounded-md text-gray-300 hover:text-white hover:bg-gray-700 transition"
    >
      {name}
    </Link>
  );
}
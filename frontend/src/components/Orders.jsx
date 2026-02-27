import React from 'react';
import { Search, Filter, ChevronDown, Eye } from 'lucide-react';

const Orders = () => {
  const orders = [
    { id: 'RET001', retailer: 'MedPlus Pharmacy', date: '2026 - 02 - 21', items: 12, total: '15,420', payment: 'Razorpay', status: 'Delivered', erpRef: 'ERP - 25821' },
    { id: 'RET001', retailer: 'MedPlus Pharmacy', date: '2026 - 02 - 21', items: 12, total: '15,420', payment: 'Razorpay', status: 'Dispatched', erpRef: 'ERP - 25821' },
    { id: 'RET001', retailer: 'MedPlus Pharmacy', date: '2026 - 02 - 21', items: 12, total: '15,420', payment: 'Razorpay', status: 'Confirmed', erpRef: 'ERP - 25821' },
    { id: 'RET001', retailer: 'MedPlus Pharmacy', date: '2026 - 02 - 21', items: 12, total: '15,420', payment: 'Razorpay', status: 'Pending', erpRef: 'ERP - 25821' },
    { id: 'RET001', retailer: 'MedPlus Pharmacy', date: '2026 - 02 - 21', items: 12, total: '15,420', payment: 'Razorpay', status: 'Cancelled', erpRef: 'ERP - 25821' },
  ];

  const getStatusStyles = (status) => {
    switch (status) {
      case 'Delivered':
        return 'bg-emerald-100 text-emerald-600';
      case 'Dispatched':
        return 'bg-purple-100 text-purple-600';
      case 'Confirmed':
        return 'bg-blue-100 text-blue-600';
      case 'Pending':
        return 'bg-amber-100 text-amber-600';
      case 'Cancelled':
        return 'bg-red-100 text-red-600';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen font-sans">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-700">Order Management</h1>
        <p className="text-sm text-gray-500 mt-1">Monitor and track all retailer orders with ERP sync status</p>
      </div>

      {/* Search and Filters */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 mb-6 flex flex-wrap items-center gap-4">
        <div className="relative flex-grow max-w-2xl">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search by shop name or owner..."
            className="w-full pl-10 pr-4 py-2 bg-gray-50 border-none rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none text-sm transition-all"
          />
        </div>

        <button className="p-2 text-gray-400 hover:text-emerald-500 transition-colors">
          <Filter className="w-5 h-5" />
        </button>

        <div className="relative min-w-[140px]">
          <select className="appearance-none w-full bg-white border border-gray-200 rounded-lg px-4 py-2 pr-10 text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-500 cursor-pointer">
            <option>All Status</option>
            <option>Delivered</option>
            <option>Dispatched</option>
            <option>Confirmed</option>
            <option>Pending</option>
            <option>Cancelled</option>
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4 pointer-events-none" />
        </div>
      </div>

      {/* Table Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#E5E9EC] text-gray-600 uppercase text-[11px] font-bold tracking-wider">
                <th className="px-6 py-4">Order ID</th>
                <th className="px-6 py-4">Retailer</th>
                <th className="px-6 py-4">Date</th>
                <th className="px-6 py-4">Items</th>
                <th className="px-6 py-4 text-center">Total Value</th>
                <th className="px-6 py-4">Payment</th>
                <th className="px-6 py-4 text-center">Status</th>
                <th className="px-6 py-4">ERP Ref</th>
                <th className="px-6 py-4 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {orders.map((order, index) => (
                <tr key={index} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 text-sm font-bold text-gray-800">{order.id}</td>
                  <td className="px-6 py-4 text-sm text-gray-600 font-medium">{order.retailer}</td>
                  <td className="px-6 py-4 text-sm text-gray-500 whitespace-nowrap">{order.date}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{order.items}</td>
                  <td className="px-6 py-4 text-sm text-gray-600 text-center">{order.total}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{order.payment}</td>
                  <td className="px-6 py-4 text-center">
                    <span className={`px-4 py-1.5 rounded-full text-[11px] font-bold inline-block min-w-[85px] ${getStatusStyles(order.status)}`}>
                      {order.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{order.erpRef}</td>
                  <td className="px-6 py-4 text-center">
                    <button className="text-teal-500 hover:text-teal-600 transition-colors p-1.5 rounded-full border border-teal-500">
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Orders;
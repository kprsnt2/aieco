import { useState, useEffect } from 'react';
import {
    LayoutDashboard,
    Cpu,
    Users,
    Activity,
    Settings,
    Zap,
    Database,
    MessageSquare,
    BarChart3,
    Clock,
    DollarSign,
    AlertTriangle,
    CheckCircle,
    TrendingUp
} from 'lucide-react';
import {
    LineChart,
    Line,
    AreaChart,
    Area,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell
} from 'recharts';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

// Mock data - in production, fetch from API
const usageData = [
    { time: '00:00', requests: 120, tokens: 45000 },
    { time: '04:00', requests: 80, tokens: 32000 },
    { time: '08:00', requests: 250, tokens: 98000 },
    { time: '12:00', requests: 420, tokens: 156000 },
    { time: '16:00', requests: 380, tokens: 142000 },
    { time: '20:00', requests: 290, tokens: 108000 },
];

const modelUsage = [
    { name: 'GLM-4.7', value: 75, color: '#667eea' },
    { name: 'Local', value: 20, color: '#10b981' },
    { name: 'Fallback', value: 5, color: '#f59e0b' },
];

const agentStats = [
    { name: 'Code Agent', runs: 245, success: 98 },
    { name: 'Research Agent', runs: 156, success: 95 },
    { name: 'File Agent', runs: 89, success: 99 },
    { name: 'Custom', runs: 34, success: 91 },
];

function App() {
    const [activeTab, setActiveTab] = useState('overview');
    const [stats, setStats] = useState({
        totalRequests: 15234,
        activeUsers: 23,
        tokensUsed: 4.2,
        avgLatency: 1.8,
        uptime: 99.9,
        costSaved: 2840
    });

    const [systemHealth, setSystemHealth] = useState({
        api: 'healthy',
        model: 'healthy',
        database: 'healthy',
        redis: 'healthy'
    });

    const tabs = [
        { id: 'overview', label: 'Overview', icon: LayoutDashboard },
        { id: 'models', label: 'Models', icon: Cpu },
        { id: 'agents', label: 'Agents', icon: Zap },
        { id: 'users', label: 'Users', icon: Users },
        { id: 'settings', label: 'Settings', icon: Settings },
    ];

    return (
        <div className="flex min-h-screen">
            {/* Sidebar */}
            <aside className="w-64 glass border-r border-white/5 p-4 flex flex-col">
                <div className="flex items-center gap-3 mb-8">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                        <Cpu size={22} />
                    </div>
                    <div>
                        <h1 className="font-bold gradient-text">AIEco</h1>
                        <p className="text-xs text-zinc-500">Dashboard</p>
                    </div>
                </div>

                <nav className="flex-1 space-y-1">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${activeTab === tab.id
                                    ? 'bg-white/10 text-white'
                                    : 'text-zinc-400 hover:bg-white/5 hover:text-white'
                                }`}
                        >
                            <tab.icon size={18} />
                            <span>{tab.label}</span>
                        </button>
                    ))}
                </nav>

                {/* System Health */}
                <div className="mt-auto pt-4 border-t border-white/5">
                    <p className="text-xs text-zinc-500 mb-2">System Health</p>
                    <div className="space-y-1">
                        {Object.entries(systemHealth).map(([key, status]) => (
                            <div key={key} className="flex items-center gap-2 text-sm">
                                <div className={`w-2 h-2 rounded-full ${status === 'healthy' ? 'bg-emerald-400' : 'bg-red-400'
                                    }`} />
                                <span className="capitalize text-zinc-400">{key}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 p-6 overflow-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-2xl font-bold">
                            {tabs.find(t => t.id === activeTab)?.label}
                        </h2>
                        <p className="text-zinc-500">Welcome back! Here's your AI ecosystem status.</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-sm text-zinc-500">Last updated: Just now</span>
                        <button className="p-2 rounded-lg hover:bg-white/10 transition-colors">
                            <Activity size={18} />
                        </button>
                    </div>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    <StatCard
                        title="Total Requests"
                        value={stats.totalRequests.toLocaleString()}
                        change="+12.5%"
                        icon={MessageSquare}
                        color="purple"
                    />
                    <StatCard
                        title="Active Users"
                        value={stats.activeUsers.toString()}
                        change="+3"
                        icon={Users}
                        color="green"
                    />
                    <StatCard
                        title="Tokens Used"
                        value={`${stats.tokensUsed}M`}
                        change="+8.2%"
                        icon={Database}
                        color="yellow"
                    />
                    <StatCard
                        title="Cost Saved"
                        value={`$${stats.costSaved}`}
                        change="vs API"
                        icon={DollarSign}
                        color="green"
                    />
                </div>

                {/* Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                    {/* Usage Chart */}
                    <div className="glass rounded-xl p-4">
                        <h3 className="font-semibold mb-4">API Usage (24h)</h3>
                        <ResponsiveContainer width="100%" height={250}>
                            <AreaChart data={usageData}>
                                <defs>
                                    <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#667eea" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#667eea" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                                <XAxis dataKey="time" stroke="#666" />
                                <YAxis stroke="#666" />
                                <Tooltip
                                    contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="requests"
                                    stroke="#667eea"
                                    fill="url(#colorRequests)"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Model Distribution */}
                    <div className="glass rounded-xl p-4">
                        <h3 className="font-semibold mb-4">Model Usage Distribution</h3>
                        <div className="flex items-center justify-center h-[250px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={modelUsage}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={80}
                                        dataKey="value"
                                        label={({ name, value }) => `${name}: ${value}%`}
                                    >
                                        {modelUsage.map((entry, index) => (
                                            <Cell key={index} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>

                {/* Agent Performance & Recent Activity */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Agent Performance */}
                    <div className="glass rounded-xl p-4">
                        <h3 className="font-semibold mb-4">Agent Performance</h3>
                        <div className="space-y-3">
                            {agentStats.map((agent) => (
                                <div key={agent.name} className="flex items-center gap-4">
                                    <div className="flex-1">
                                        <div className="flex justify-between mb-1">
                                            <span className="text-sm">{agent.name}</span>
                                            <span className="text-xs text-zinc-500">{agent.runs} runs</span>
                                        </div>
                                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                                                style={{ width: `${agent.success}%` }}
                                            />
                                        </div>
                                    </div>
                                    <span className="text-sm text-emerald-400">{agent.success}%</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Quick Actions */}
                    <div className="glass rounded-xl p-4">
                        <h3 className="font-semibold mb-4">Quick Actions</h3>
                        <div className="grid grid-cols-2 gap-3">
                            <ActionButton icon={Cpu} label="Restart Model" />
                            <ActionButton icon={Database} label="Clear Cache" />
                            <ActionButton icon={Users} label="Invite User" />
                            <ActionButton icon={BarChart3} label="Export Report" />
                        </div>

                        <div className="mt-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                            <div className="flex items-center gap-2 text-emerald-400">
                                <CheckCircle size={18} />
                                <span className="font-medium">All systems operational</span>
                            </div>
                            <p className="text-xs text-zinc-400 mt-1">
                                GLM-4.7 358B running on 4x MI300X • 768GB VRAM
                            </p>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

function StatCard({ title, value, change, icon: Icon, color }: {
    title: string;
    value: string;
    change: string;
    icon: any;
    color: 'purple' | 'green' | 'yellow' | 'red';
}) {
    const colorClasses = {
        purple: 'stat-card',
        green: 'stat-green',
        yellow: 'stat-yellow',
        red: 'stat-red'
    };

    return (
        <div className={`${colorClasses[color]} rounded-xl p-4`}>
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-sm text-zinc-400">{title}</p>
                    <p className="text-2xl font-bold mt-1">{value}</p>
                    <div className="flex items-center gap-1 mt-1">
                        <TrendingUp size={14} className="text-emerald-400" />
                        <span className="text-xs text-emerald-400">{change}</span>
                    </div>
                </div>
                <div className="p-2 rounded-lg bg-white/10">
                    <Icon size={20} />
                </div>
            </div>
        </div>
    );
}

function ActionButton({ icon: Icon, label }: { icon: any; label: string }) {
    return (
        <button className="flex items-center gap-2 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-sm">
            <Icon size={16} />
            <span>{label}</span>
        </button>
    );
}

export default App;

'use client';

import { useState } from 'react';
import { apiClient, ListingData, MatchResult } from '@/lib/api-client';
import PropertyMap from '@/components/PropertyMap';

export default function Home() {
    const [activeTab, setActiveTab] = useState<'attributes' | 'address'>('address');

    // Attribute Search State
    const [formData, setFormData] = useState<ListingData>({
        settlement: '',
        parcel_area_m2: 0,
        construction_year: undefined,
        net_floor_area_m2: undefined,
        property_type: 'Hiša',
        street_name: '',
    });

    // Address Search State
    const [addressQuery, setAddressQuery] = useState('');
    const [addressSuggestions, setAddressSuggestions] = useState<any[]>([]);

    // Results
    const [result, setResult] = useState<MatchResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

    // Address Autocomplete
    const handleAddressInput = async (query: string) => {
        setAddressQuery(query);
        if (query.length < 3) {
            setAddressSuggestions([]);
            return;
        }

        try {
            const res = await fetch(
                `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?country=si&access_token=${MAPBOX_TOKEN}&types=address`
            );
            const data = await res.json();
            setAddressSuggestions(data.features || []);
        } catch (err) {
            console.error('Geocoding error:', err);
        }
    };

    const handleSelectAddress = (feature: any) => {
        setAddressQuery(feature.place_name);
        setAddressSuggestions([]);
        handleAddressSearch(feature);
    };

    const handleAddressSearch = async (feature: any) => {
        setLoading(true);
        setError(null);
        try {
            const [lng, lat] = feature.center;
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/find-parcel-by-point`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lng, lat, address: feature.place_name })
            });

            if (!res.ok) throw new Error('Search failed');
            const data = await res.json();
            setResult(data);
        } catch (err: any) {
            setError(err.message || 'Failed to find parcel at this address');
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteMapClick = async (lng: number, lat: number) => {
        const mockFeature = {
            center: [lng, lat],
            place_name: 'Selected Location'
        };
        handleAddressSearch(mockFeature);
    };

    const handleSubmitAttributes = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const matchResult = await apiClient.findProbableParcels(formData);
            setResult(matchResult);
        } catch (err: any) {
            setError(err.message || 'Failed to find parcels');
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="flex h-screen w-screen overflow-hidden bg-gray-100">
            {/* Sidebar */}
            <div className="w-[450px] flex flex-col bg-white shadow-xl z-20 h-full border-r border-gray-200">
                {/* Header */}
                <div className="p-5 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
                    <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                        <span className="text-blue-600">GNEP</span>
                        <span className="text-gray-300">|</span>
                        <span className="text-sm font-medium text-gray-600">Property Intelligence</span>
                    </h1>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-gray-200">
                    <button
                        className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === 'address' ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50' : 'text-gray-500 hover:bg-gray-50'}`}
                        onClick={() => setActiveTab('address')}
                    >
                        🏠 Address / Map
                    </button>
                    <button
                        className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === 'attributes' ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50' : 'text-gray-500 hover:bg-gray-50'}`}
                        onClick={() => setActiveTab('attributes')}
                    >
                        📋 Attributes
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-5 scrollbar-thin">
                    <div className="mb-6">
                        {activeTab === 'address' ? (
                            <div className="space-y-4 relative">
                                <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">
                                    Search Location
                                </label>
                                <input
                                    type="text"
                                    value={addressQuery}
                                    onChange={(e) => handleAddressInput(e.target.value)}
                                    placeholder="Type address..."
                                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm"
                                />
                                {addressSuggestions.length > 0 && (
                                    <div className="absolute z-30 w-full bg-white border border-gray-100 mt-1 rounded-lg shadow-xl max-h-60 overflow-y-auto">
                                        {addressSuggestions.map((s) => (
                                            <div
                                                key={s.id}
                                                className="px-4 py-3 hover:bg-blue-50 cursor-pointer text-sm border-b border-gray-50 last:border-0"
                                                onClick={() => handleSelectAddress(s)}
                                            >
                                                {s.place_name}
                                            </div>
                                        ))}
                                    </div>
                                )}
                                <p className="text-xs text-blue-600 bg-blue-50 p-2 rounded border border-blue-100">
                                    👆 <b>Pro Tip:</b> Click anywhere on the map to identify a parcel instantly.
                                </p>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmitAttributes} className="space-y-5">
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Settlement</label>
                                        <input
                                            type="text"
                                            required
                                            value={formData.settlement}
                                            onChange={(e) => setFormData({ ...formData, settlement: e.target.value })}
                                            placeholder="e.g. Ljubljana"
                                            className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                                        />
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Area (m²)</label>
                                            <input
                                                type="number"
                                                required
                                                value={formData.parcel_area_m2 || ''}
                                                onChange={(e) => setFormData({ ...formData, parcel_area_m2: parseFloat(e.target.value) })}
                                                placeholder="500"
                                                className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">Year</label>
                                            <input
                                                type="number"
                                                value={formData.construction_year || ''}
                                                onChange={(e) => setFormData({ ...formData, construction_year: parseInt(e.target.value) })}
                                                placeholder="1980"
                                                className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                                            />
                                        </div>
                                    </div>
                                </div>
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg shadow-md transition-all text-sm"
                                >
                                    {loading ? 'Analyzing...' : 'Find Matches'}
                                </button>
                            </form>
                        )}
                    </div>

                    {error && (
                        <div className="p-3 bg-red-50 border border-red-200 rounded-lg mb-4 text-xs text-red-700">
                            {error}
                        </div>
                    )}

                    {result && (
                        <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-sm font-bold text-gray-900 uppercase tracking-wider">Results</h2>
                                <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full border border-gray-200">{result.count} Found</span>
                            </div>

                            {result.matches.length > 0 ? (
                                <div className="space-y-3 pb-4">
                                    {result.matches.map((match, idx) => (
                                        <div
                                            key={idx}
                                            className={`p-3 rounded-lg border transition-all cursor-pointer hover:shadow-md ${match.confidence > 90
                                                    ? 'bg-green-50/30 border-green-200 hover:border-green-300'
                                                    : 'bg-white border-gray-200 hover:border-blue-300'
                                                }`}
                                        >
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <div className="text-[10px] font-bold text-gray-400 uppercase">Parcel</div>
                                                    <div className="font-mono text-base font-bold text-gray-900 leading-tight">{match.parcela.parcela_stevilka}</div>
                                                    <div className="text-xs text-gray-500 mt-0.5">KO {match.parcela.ko_ime}</div>
                                                </div>
                                                <div className={`text-lg font-bold ${match.confidence > 90 ? 'text-green-600' : 'text-blue-600'}`}>
                                                    {match.confidence.toFixed(0)}%
                                                </div>
                                            </div>
                                            <div className="mt-2 pt-2 border-t border-gray-100 flex gap-4 text-xs text-gray-600">
                                                <span><b>Area:</b> {match.parcela.povrsina}m²</span>
                                                {match.stavba && <span><b>Bldg:</b> Yes</span>}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-8 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                                    <p className="text-gray-400 text-sm">No parcels found.</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* MAIN MAP */}
            <div className="flex-1 h-full relative bg-gray-200">
                <PropertyMap
                    geojson={result?.geojson}
                    onMapClick={handleDeleteMapClick}
                />

                {loading && (
                    <div className="absolute top-4 right-4 bg-white/90 backdrop-blur px-4 py-2 rounded-full shadow-lg z-10 flex items-center gap-2">
                        <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                        <span className="text-sm font-medium text-blue-900">Processing...</span>
                    </div>
                )}
            </div>
        </main>
    );
}

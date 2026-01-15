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
        property_type: '',
        street_name: '',
    });

    // Address Search State
    const [addressQuery, setAddressQuery] = useState('');
    const [addressSuggestions, setAddressSuggestions] = useState<any[]>([]);
    const [selectedAddress, setSelectedAddress] = useState<any>(null);

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
        setSelectedAddress(feature);
        setAddressSuggestions([]);
        // Auto-search when address selected
        handleAddressSearch(feature);
    };

    const handleAddressSearch = async (feature: any) => {
        setLoading(true);
        setError(null);
        try {
            const [lng, lat] = feature.center;
            // Call new backend endpoint for coordinate search
            // For now, we simulate or use existing if adaptable, but we need a new endpoint really.
            // Let's assume we will build /api/find-parcel-by-point
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
        <main className="min-h-screen bg-gray-50">
            <div className="container mx-auto px-4 py-8">
                <header className="mb-8 text-center">
                    <h1 className="text-4xl font-bold text-gray-900 mb-2">
                        GNEP - AI Real Estate Locator
                    </h1>
                    <p className="text-gray-600">
                        Automatically match listings with GURS cadastral data
                    </p>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Search Panel */}
                    <div className="bg-white rounded-lg shadow-md overflow-hidden">
                        {/* Tabs */}
                        <div className="flex border-b">
                            <button
                                className={`flex-1 py-4 font-medium text-sm ${activeTab === 'address' ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                                onClick={() => setActiveTab('address')}
                            >
                                🏠 Search by Address
                            </button>
                            <button
                                className={`flex-1 py-4 font-medium text-sm ${activeTab === 'attributes' ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                                onClick={() => setActiveTab('attributes')}
                            >
                                📋 Attribute Match
                            </button>
                        </div>

                        <div className="p-6">
                            {activeTab === 'address' ? (
                                <div className="space-y-4">
                                    <div className="relative">
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            Enter Address (Slovenia)
                                        </label>
                                        <input
                                            type="text"
                                            value={addressQuery}
                                            onChange={(e) => handleAddressInput(e.target.value)}
                                            placeholder="e.g. Tržaška cesta 25, Ljubljana"
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm"
                                        />

                                        {/* Suggestions Dropdown */}
                                        {addressSuggestions.length > 0 && (
                                            <div className="absolute z-10 w-full bg-white border border-gray-200 mt-1 rounded-md shadow-lg max-h-60 overflow-y-auto">
                                                {addressSuggestions.map((suggestion) => (
                                                    <div
                                                        key={suggestion.id}
                                                        className="px-4 py-2 hover:bg-gray-100 cursor-pointer text-sm"
                                                        onClick={() => handleSelectAddress(suggestion)}
                                                    >
                                                        {suggestion.place_name}
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                    <p className="text-xs text-gray-500">
                                        Powered by Mapbox Geocoding. Select an address to instantly find the parcel.
                                    </p>
                                </div>
                            ) : (
                                <form onSubmit={handleSubmitAttributes} className="space-y-4">
                                    {/* Existing Attribute Form */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            Settlement *
                                        </label>
                                        <input
                                            type="text"
                                            required
                                            value={formData.settlement}
                                            onChange={(e) => setFormData({ ...formData, settlement: e.target.value })}
                                            placeholder="Ljubljana - Center"
                                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            Parcel Area (m²) *
                                        </label>
                                        <input
                                            type="number"
                                            required
                                            value={formData.parcel_area_m2 || ''}
                                            onChange={(e) => setFormData({ ...formData, parcel_area_m2: parseFloat(e.target.value) })}
                                            placeholder="542"
                                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        />
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                                            <input
                                                type="number"
                                                value={formData.construction_year || ''}
                                                onChange={(e) => setFormData({ ...formData, construction_year: parseInt(e.target.value) })}
                                                placeholder="1974"
                                                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">Net Area</label>
                                            <input
                                                type="number"
                                                step="0.1"
                                                value={formData.net_floor_area_m2 || ''}
                                                onChange={(e) => setFormData({ ...formData, net_floor_area_m2: parseFloat(e.target.value) })}
                                                placeholder="185.4"
                                                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                                            />
                                        </div>
                                    </div>

                                    <button
                                        type="submit"
                                        disabled={loading}
                                        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition"
                                    >
                                        {loading ? 'Searching...' : 'Find Probable Parcels'}
                                    </button>
                                </form>
                            )}

                            {error && (
                                <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">
                                    {error}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Results */}
                    <div>
                        <div className="bg-white rounded-lg shadow-md p-6 mb-4">
                            <h2 className="text-2xl font-semibold mb-4">Results</h2>

                            {result && result.success ? (
                                <div>
                                    <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
                                        {result.message}
                                    </div>

                                    {result.matches.length > 0 ? (
                                        <div className="space-y-3">
                                            {result.matches.map((match, idx) => (
                                                <div key={idx} className="border rounded-lg p-4 flex justify-between items-center transition hover:bg-gray-50 cursor-pointer">
                                                    <div>
                                                        <h3 className="font-bold text-gray-900">
                                                            Parcela {match.parcela.parcela_stevilka}
                                                        </h3>
                                                        <p className="text-sm text-gray-600">
                                                            KO {match.parcela.ko_ime} ({match.parcela.ko_sifra})
                                                        </p>
                                                        <p className="text-xs text-gray-500 mt-1">
                                                            Area: {match.parcela.povrsina}m²
                                                        </p>
                                                    </div>
                                                    <span className={`text-lg font-bold ${match.confidence > 80 ? 'text-green-600' : 'text-blue-600'}`}>
                                                        {match.confidence.toFixed(0)}%
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="text-gray-600 italic">No exact parcel match found at this location.</p>
                                    )}
                                </div>
                            ) : (
                                !loading && <p className="text-gray-500">
                                    {activeTab === 'address'
                                        ? 'Start typing an address to find a parcel...'
                                        : 'Enter listing data to match probable parcels...'}
                                </p>
                            )}

                            {loading && (
                                <div className="flex justify-center py-8">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                                </div>
                            )}
                        </div>

                        {/* Map */}
                        <div className="bg-white rounded-lg shadow-md overflow-hidden relative" style={{ height: '400px' }}>
                            <PropertyMap geojson={result?.geojson} />
                            {!result && activeTab === 'address' && (
                                <div className="absolute inset-0 bg-gray-50 flex items-center justify-center bg-opacity-50 pointer-events-none">
                                    <p className="text-gray-400 font-medium">Map will update when address is selected</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-700 font-medium transition"
                        >
                FutureCode.si
            </a>
        </p>
                </footer >
            </div >
        </main >
    );
}

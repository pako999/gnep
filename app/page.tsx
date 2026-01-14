'use client';

import { useState } from 'react';
import { apiClient, ListingData, MatchResult } from '@/lib/api-client';
import PropertyMap from '@/components/PropertyMap';

export default function Home() {
    const [formData, setFormData] = useState<ListingData>({
        settlement: '',
        parcel_area_m2: 0,
        construction_year: undefined,
        net_floor_area_m2: undefined,
        property_type: '',
        street_name: '',
    });

    const [result, setResult] = useState<MatchResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
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
                <h1 className="text-4xl font-bold text-gray-900 mb-2">
                    GNEP - AI Real Estate Locator
                </h1>
                <p className="text-gray-600 mb-8">
                    Automatically match listings with GURS cadastral data
                </p>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Search Form */}
                    <div className="bg-white rounded-lg shadow-md p-6">
                        <h2 className="text-2xl font-semibold mb-4">Listing Data</h2>

                        <form onSubmit={handleSubmit} className="space-y-4">
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

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Construction Year
                                </label>
                                <input
                                    type="number"
                                    value={formData.construction_year || ''}
                                    onChange={(e) => setFormData({ ...formData, construction_year: parseInt(e.target.value) })}
                                    placeholder="1974"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Net Floor Area (m²)
                                </label>
                                <input
                                    type="number"
                                    step="0.1"
                                    value={formData.net_floor_area_m2 || ''}
                                    onChange={(e) => setFormData({ ...formData, net_floor_area_m2: parseFloat(e.target.value) })}
                                    placeholder="185.4"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Property Type
                                </label>
                                <select
                                    value={formData.property_type}
                                    onChange={(e) => setFormData({ ...formData, property_type: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="">Select type</option>
                                    <option value="Hiša">Hiša</option>
                                    <option value="Stanovanje">Stanovanje</option>
                                    <option value="Zemljišče">Zemljišče</option>
                                </select>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
                            >
                                {loading ? 'Searching...' : 'Find Probable Parcels'}
                            </button>
                        </form>

                        {error && (
                            <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                                {error}
                            </div>
                        )}
                    </div>

                    {/* Results */}
                    <div>
                        <div className="bg-white rounded-lg shadow-md p-6 mb-4">
                            <h2 className="text-2xl font-semibold mb-4">Results</h2>

                            {result && result.success && (
                                <div>
                                    <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
                                        {result.message}
                                    </div>

                                    {result.matches.length > 0 ? (
                                        <div className="space-y-3">
                                            {result.matches.map((match, idx) => (
                                                <div key={idx} className="border rounded-lg p-4">
                                                    <div className="flex justify-between items-start mb-2">
                                                        <div>
                                                            <h3 className="font-semibold">
                                                                Parcela {match.parcela.parcela_stevilka}
                                                            </h3>
                                                            <p className="text-sm text-gray-600">
                                                                {match.parcela.ko_ime}
                                                            </p>
                                                        </div>
                                                        <span className="text-lg font-bold text-green-600">
                                                            {match.confidence.toFixed(1)}%
                                                        </span>
                                                    </div>

                                                    <div className="text-sm text-gray-600">
                                                        <p>Površina: {match.parcela.povrsina}m²</p>
                                                        {match.stavba && (
                                                            <>
                                                                <p>Leto: {match.stavba.leto_izgradnje}</p>
                                                                <p>Tloris: {match.stavba.neto_tloris}m²</p>
                                                            </>
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="text-gray-600">No matches found</p>
                                    )}
                                </div>
                            )}

                            {!result && (
                                <p className="text-gray-500">Enter listing data to find matching parcels</p>
                            )}
                        </div>

                        {/* Map */}
                        <div className="bg-white rounded-lg shadow-md overflow-hidden" style={{ height: '400px' }}>
                            <PropertyMap geojson={result?.geojson} />
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <footer className="mt-16 pt-8 border-t border-gray-200 text-center">
                    <p className="text-sm text-gray-600">
                        Built by{' '}
                        <a
                            href="https://futurecode.si"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-700 font-medium transition"
                        >
                            FutureCode.si
                        </a>
                    </p>
                </footer>
            </div>
        </main>
    );
}

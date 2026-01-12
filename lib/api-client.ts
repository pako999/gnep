// API Client for GNEP Backend
// Handles communication between Vercel Frontend and Render Backend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ListingData {
    settlement: string;
    parcel_area_m2: number;
    construction_year?: number;
    net_floor_area_m2?: number;
    property_type?: string;
    street_name?: string;
}

export interface MatchResult {
    success: boolean;
    message: string;
    matches: Array<{
        parcela: {
            id: number;
            parcela_stevilka: string;
            ko_ime: string;
            ko_sifra: string;
            povrsina: number;
        };
        stavba?: {
            id: number;
            leto_izgradnje?: number;
            neto_tloris?: number;
            naslov?: string;
        };
        confidence: number;
        score: number;
        score_breakdown: Record<string, number>;
    }>;
    geojson: any;
    count: number;
}

class APIClient {
    private baseURL: string;

    constructor(baseURL: string = API_BASE_URL) {
        this.baseURL = baseURL;
    }

    /**
     * Find probable parcels matching listing data
     */
    async findProbableParcels(listingData: ListingData): Promise<MatchResult> {
        const response = await fetch(`${this.baseURL}/api/find-probable-parcels`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(listingData),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to find probable parcels');
        }

        return response.json();
    }

    /**
     * Check building permit status (placeholder)
     */
    async checkPermit(listingData: ListingData): Promise<any> {
        const response = await fetch(`${this.baseURL}/api/check-permit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(listingData),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to check permit');
        }

        return response.json();
    }

    /**
     * Get parcel details by ID
     */
    async getParcelDetails(parcelaId: number): Promise<any> {
        const response = await fetch(`${this.baseURL}/api/parcels/${parcelaId}`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get parcel details');
        }

        return response.json();
    }

    /**
     * Health check
     */
    async healthCheck(): Promise<any> {
        const response = await fetch(`${this.baseURL}/health`);
        return response.json();
    }
}

// Export singleton instance
export const apiClient = new APIClient();
export default apiClient;

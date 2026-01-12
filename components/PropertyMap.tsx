'use client';

import { useState } from 'react';
import Map, { Source, Layer, NavigationControl } from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

interface PropertyMapProps {
    geojson?: any;
    center?: [number, number];
    zoom?: number;
}

export default function PropertyMap({
    geojson,
    center = [14.5, 46.05], // Slovenia center
    zoom = 8
}: PropertyMapProps) {
    const [viewState, setViewState] = useState({
        longitude: center[0],
        latitude: center[1],
        zoom: zoom
    });

    const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

    if (!mapboxToken) {
        return (
            <div className="w-full h-full flex items-center justify-center bg-gray-100">
                <p className="text-gray-600">Mapbox token not configured</p>
            </div>
        );
    }

    return (
        <Map
            {...viewState}
            onMove={evt => setViewState(evt.viewState)}
            mapboxAccessToken={mapboxToken}
            style={{ width: '100%', height: '100%' }}
            mapStyle="mapbox://styles/mapbox/streets-v12"
        >
            <NavigationControl position="top-right" />

            {geojson && (
                <Source id="parcels" type="geojson" data={geojson}>
                    <Layer
                        id="parcel-fills"
                        type="fill"
                        paint={{
                            'fill-color': ['get', 'color'],
                            'fill-opacity': ['get', 'opacity']
                        }}
                    />
                    <Layer
                        id="parcel-borders"
                        type="line"
                        paint={{
                            'line-color': '#000',
                            'line-width': 2
                        }}
                    />
                </Source>
            )}
        </Map>
    );
}

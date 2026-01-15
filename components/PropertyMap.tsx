'use client';

import { useState } from 'react';
import Map, { Source, Layer, NavigationControl } from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';


interface PropertyMapProps {
    geojson?: any;
    center?: [number, number];
    zoom?: number;
    onMapClick?: (lng: number, lat: number) => void;
}

export default function PropertyMap({
    geojson,
    center = [14.5, 46.05], // Slovenia center
    zoom = 8,
    onMapClick
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
            onClick={evt => onMapClick && onMapClick(evt.lngLat.lng, evt.lngLat.lat)}
            mapboxAccessToken={mapboxToken}
            style={{ width: '100%', height: '100%' }}
            mapStyle="mapbox://styles/mapbox/satellite-streets-v12"
            cursor={onMapClick ? 'crosshair' : 'auto'}
        >
            <NavigationControl position="top-right" />

            {/* Cadastral Layer (Vector Tiles) */}
            <Source
                id="cadastre-source"
                type="vector"
                tiles={[
                    `${process.env.NEXT_PUBLIC_API_URL || ''}/api/tiles/parcels/{z}/{x}/{y}`
                ]}
                minzoom={14}
                maxzoom={21}
            >
                <Layer
                    id="cadastre-lines"
                    type="line"
                    source-layer="default"
                    paint={{
                        'line-color': '#eab308', // Yellow like gov site
                        'line-width': 1,
                        'line-opacity': 0.8
                    }}
                />
            </Source>

            {geojson && (
                <Source id="parcels" type="geojson" data={geojson}>
                    <Layer
                        id="parcel-fills"
                        type="fill"
                        paint={{
                            'fill-color': '#3b82f6',
                            'fill-opacity': 0.4
                        }}
                    />
                    <Layer
                        id="parcel-borders"
                        type="line"
                        paint={{
                            'line-color': '#1d4ed8',
                            'line-width': 2
                        }}
                    />
                </Source>
            )}
        </Map>
    );
}

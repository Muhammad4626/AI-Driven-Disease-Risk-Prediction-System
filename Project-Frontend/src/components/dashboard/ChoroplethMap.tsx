import React, { useRef, useEffect, useCallback, useMemo, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useDashboard } from '../../context/DashboardContext';
import { buildDistrictRiskData, getDistrictNameFromPcode, type DistrictRiskDataAPI } from './districtRiskData';
import pakAdmin2Geo from '../../assets/map_boundaries/pak_admin2_em.json';

type GeoJSONFeature = GeoJSON.Feature<GeoJSON.Geometry> & {
  properties?: Record<string, unknown> & { adm2_pcode?: string };
};
type GeoJSONFC = GeoJSON.FeatureCollection & { features: GeoJSONFeature[] };

export interface ChoroplethMapProps {
  className?: string;
  onDataReady?: (data: DistrictRiskDataAPI) => void;
}

export function ChoroplethMap({ className, onDataReady }: ChoroplethMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const { selectedDisease, setActiveDistrictPCode, setActiveDistrictName } = useDashboard();

  const [riskData, setRiskData] = useState<DistrictRiskDataAPI | null>(null);
  const [geojsonWithRisk, setGeojsonWithRisk] = useState<GeoJSONFC | null>(null);

  // Load risk data asynchronously
  useEffect(() => {
    async function loadRiskData() {
      const raw = pakAdmin2Geo as GeoJSONFC;
      if (!raw?.features?.length) return;

      const pcodes = raw.features.map(
        (f) => f.properties?.adm2_pcode ?? (f as unknown as { id?: string }).id ?? `DIST_${raw.features.indexOf(f)}`
      );

      const api = await buildDistrictRiskData(pcodes);

      const features = raw.features.map((f, i) => {
        const pcode = f.properties?.adm2_pcode ?? (f as unknown as { id?: string }).id ?? `DIST_${i}`;
        return {
          ...f,
          properties: {
            ...f.properties,
            adm2_pcode: pcode,
            risk_malaria: api.getRiskScore(pcode, 'malaria'),
            risk_diarrhea: api.getRiskScore(pcode, 'diarrhea'),
            risk_typhoid: api.getRiskScore(pcode, 'typhoid'),
          },
        };
      });

      const enrichedGeoJSON: GeoJSONFC = { type: 'FeatureCollection', features };

      setGeojsonWithRisk(enrichedGeoJSON);
      setRiskData(api);

      if (onDataReady) onDataReady(api);
    }

    loadRiskData();
  }, [onDataReady]);

  // Initialize map
  useEffect(() => {
    if (!containerRef.current || !geojsonWithRisk?.features?.length || !riskData) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {},
        layers: [
          {
            id: 'background',
            type: 'background',
            paint: { 'background-color': '#f0f4f8' },
          },
        ],
      },
      center: [69.3, 30.4],
      zoom: 5,
    });

    map.on('load', () => {
      map.addSource('districts', {
        type: 'geojson',
        data: geojsonWithRisk,
        promoteId: 'adm2_pcode',
      });

      const riskKey = `risk_${selectedDisease}` as 'risk_malaria' | 'risk_diarrhea' | 'risk_typhoid';

      map.addLayer({
        id: 'districts-fill',
        type: 'fill',
        source: 'districts',
        paint: {
          'fill-color': [
            'interpolate',
            ['linear'],
            ['get', riskKey],
            0,   '#22c55e',   // Green
            5,   '#86efac',   // Light Green
            10,  '#eab308',   // Yellow
            15,  '#f59e0b',   // Orange
            18,  '#ef4444',   // Red
            22,  '#b91c1c'    // Dark Red
          ],
            'fill-opacity': 0.85,
            'fill-outline-color': '#64748b',
        },
      });

      map.addLayer({
        id: 'districts-hover',
        type: 'fill',
        source: 'districts',
        paint: {
          'fill-color': 'transparent',
          'fill-opacity': 0,
        },
      });
    });

    const onMapClick = (e: maplibregl.MapMouseEvent) => {
      const features = map.queryRenderedFeatures(e.point, { layers: ['districts-fill'] });
      if (features.length) {
        const id = features[0].id ?? features[0].properties?.adm2_pcode;
        if (id != null) {
          const pcode = String(id);
          setActiveDistrictPCode(pcode);
          setActiveDistrictName(getDistrictNameFromPcode(pcode));
        }
      }
    };
    map.on('click', onMapClick);

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [geojsonWithRisk, riskData, selectedDisease, setActiveDistrictName, setActiveDistrictPCode]);

  // Update map colors when disease changes
  useEffect(() => {
  const map = mapRef.current;
  if (!map || !map.getLayer('districts-fill')) return;

  const riskKey = `risk_${selectedDisease}`;
  map.setPaintProperty('districts-fill', 'fill-color', [
    'interpolate',
    ['linear'],
    ['get', riskKey],
    0,   '#22c55e',
    5,   '#86efac',
    10,  '#eab308',
    15,  '#f59e0b',
    18,  '#ef4444',
    22,  '#b91c1c'
  ]);
}, [selectedDisease]);

  return <div ref={containerRef} className={className} style={{ width: '100%', height: '100%', minHeight: 360 }} />;
}
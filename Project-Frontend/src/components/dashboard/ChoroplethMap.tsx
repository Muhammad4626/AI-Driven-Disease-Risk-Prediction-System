import React, { useRef, useEffect, useCallback, useMemo } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useDashboard } from '../../context/DashboardContext';
import { buildDistrictRiskData, type DistrictRiskDataAPI } from './districtRiskData';
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
  const { selectedDisease, setActiveDistrictPCode } = useDashboard();

  const { geojsonWithRisk, riskData } = useMemo(() => {
    const raw = pakAdmin2Geo as GeoJSONFC;
    if (!raw?.features?.length) {
      return { geojsonWithRisk: raw, riskData: null };
    }
    const pcodes = raw.features.map(
      (f) => f.properties?.adm2_pcode ?? (f as unknown as { id?: string }).id ?? `DIST_${raw.features.indexOf(f)}`
    );
    const api = buildDistrictRiskData(pcodes);
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
    const geojsonWithRisk: GeoJSONFC = { type: 'FeatureCollection', features };
    return { geojsonWithRisk, riskData: api };
  }, []);

  useEffect(() => {
    if (riskData) onDataReady?.(riskData);
  }, [riskData, onDataReady]);

  useEffect(() => {
    if (!containerRef.current || !geojsonWithRisk?.features?.length) return;

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
        data: geojsonWithRisk as GeoJSON.FeatureCollection,
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
            0, '#22c55e',
            30, '#eab308',
            50, '#ea580c',
            70, '#dc2626',
            100, '#991b1b',
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
        if (id != null) setActiveDistrictPCode(String(id));
      }
    };
    map.on('click', onMapClick);

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getLayer('districts-fill')) return;
    const riskKey = `risk_${selectedDisease}`;
    map.setPaintProperty('districts-fill', 'fill-color', [
      'interpolate',
      ['linear'],
      ['get', riskKey],
      0, '#22c55e',
      30, '#eab308',
      50, '#ea580c',
      70, '#dc2626',
      100, '#991b1b',
    ]);
  }, [selectedDisease]);

  return <div ref={containerRef} className={className} style={{ width: '100%', height: '100%', minHeight: 360 }} />;
}

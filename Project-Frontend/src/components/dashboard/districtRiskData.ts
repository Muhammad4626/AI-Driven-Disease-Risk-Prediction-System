import type { DiseaseKey } from '../../context/DashboardContext';
import { getAllDistrictRisks, getDistrictHistory } from '../../services/predictionService';

// Full pcode to district_name mapping from your GeoJSON
const pcodeToDistrict: Record<string, string> = {
  "PK101": "Bagh",
  "PK102": "Bhimber",
  "PK103": "Jhelum Valley",
  "PK104": "Haveli",
  "PK105": "Kotli",
  "PK106": "Mirpur",
  "PK107": "Muzaffarabad",
  "PK108": "Neelum",
  "PK109": "Poonch",
  "PK110": "Sudhnoti",
  "PK201": "Awaran",
  "PK202": "Barkhan",
  "PK203": "Chagai",
  "PK204": "Dera Bugti",
  "PK205": "Gwadar",
  "PK206": "Harnai",
  "PK207": "Jaffarabad",
  "PK208": "Jhal Magsi",
  "PK209": "Kachhi",
  "PK210": "Kalat",
  "PK211": "Kech",
  "PK212": "Kharan",
  "PK213": "Khuzdar",
  "PK214": "Killa Abdullah",
  "PK215": "Killa Saifullah",
  "PK216": "Kohlu",
  "PK217": "Lasbela",
  "PK218": "Lehri",
  "PK219": "Loralai",
  "PK220": "Mastung",
  "PK221": "Musakhel",
  "PK222": "Nasirabad",
  "PK223": "Nushki",
  "PK224": "Panjgur",
  "PK225": "Pishin",
  "PK226": "Quetta",
  "PK227": "Sherani",
  "PK228": "Sibi",
  "PK229": "Sohbatpur",
  "PK230": "Washuk",
  "PK231": "Zhob",
  "PK232": "Ziarat",
  "PK233": "Shaheed Sikandarabad",
  "PK234": "Duki",
  "PK235": "Chaman",
  "PK301": "Astore",
  "PK302": "Diamir",
  "PK303": "Ghanche",
  "PK304": "Ghizer",
  "PK305": "Gilgit",
  "PK306": "Hunza",
  "PK307": "Skardu",
  "PK308": "Nagar",
  "PK309": "Kharmang",
  "PK310": "Shigar",
  "PK311": "Darel",
  "PK312": "Tangir",
  "PK313": "Gupis-Yasin",
  "PK314": "Rondu",
  "PK401": "Islamabad",
  "PK501": "Abbottabad",
  "PK502": "Bajaur",
  "PK503": "Bannu",
  "PK504": "Batagram",
  "PK505": "Buner",
  "PK506": "Charsadda",
  "PK507": "Chitral Lower",
  "PK508": "Chitral Upper",
  "PK509": "D. I. Khan",
  "PK510": "Hangu",
  "PK511": "Haripur",
  "PK512": "Karak",
  "PK513": "Khyber",
  "PK514": "Kohat",
  "PK515": "Kohistan Lower",
  "PK516": "Kohistan Upper",
  "PK517": "Kolai Palas Kohistan",
  "PK518": "Kurram",
  "PK519": "Lakki Marwat",
  "PK520": "Lower Dir",
  "PK521": "Malakand",
  "PK522": "Mansehra",
  "PK523": "Mardan",
  "PK524": "Mohmand",
  "PK525": "North Waziristan",
  "PK526": "Nowshera",
  "PK527": "Orakzai",
  "PK528": "Peshawar",
  "PK529": "Shangla",
  "PK530": "South Waziristan",
  "PK531": "Swabi",
  "PK532": "Swat",
  "PK533": "Tank",
  "PK534": "Tor Ghar",
  "PK535": "Upper Dir",
  "PK601": "Attock",
  "PK602": "Bahawalnagar",
  "PK603": "Bahawalpur",
  "PK604": "Bhakkar",
  "PK605": "Chakwal",
  "PK606": "Chiniot",
  "PK607": "Dera Ghazi Khan",
  "PK608": "Faisalabad",
  "PK609": "Gujranwala",
  "PK610": "Gujrat",
  "PK611": "Hafizabad",
  "PK612": "Jhang",
  "PK613": "Jhelum",
  "PK614": "Kasur",
  "PK615": "Khanewal",
  "PK616": "Khushab",
  "PK617": "Lahore",
  "PK618": "Leiah",
  "PK619": "Lodhran",
  "PK620": "Mandi Bahauddin",
  "PK621": "Mianwali",
  "PK622": "Multan",
  "PK623": "Muzaffargarh",
  "PK624": "Nankana Sahib",
  "PK625": "Narowal",
  "PK626": "Okara",
  "PK627": "Pakpattan",
  "PK628": "Rahim Yar Khan",
  "PK629": "Rajanpur",
  "PK630": "Rawalpindi",
  "PK631": "Sahiwal",
  "PK632": "Sargodha",
  "PK633": "Sheikhupura",
  "PK634": "Sialkot",
  "PK635": "Toba Tek Singh",
  "PK636": "Vehari",
  "PK701": "Badin",
  "PK702": "Central Karachi",
  "PK703": "Dadu",
  "PK704": "East Karachi",
  "PK705": "Ghotki",
  "PK706": "Hyderabad",
  "PK707": "Jacobabad",
  "PK708": "Jamshoro",
  "PK709": "Kambar Shahdad Kot",
  "PK710": "Kashmore",
  "PK711": "Khairpur",
  "PK712": "Korangi Karachi",
  "PK713": "Larkana",
  "PK714": "Malir Karachi",
  "PK715": "Matiari",
  "PK716": "Mirpur Khas",
  "PK717": "Naushahro Feroze",
  "PK718": "Sanghar",
  "PK719": "Shaheed Benazir Abad",
  "PK720": "Shikarpur",
  "PK721": "South Karachi",
  "PK722": "Sujawal",
  "PK723": "Sukkur",
  "PK724": "Tando Allahyar",
  "PK725": "Tando Muhammad Khan",
  "PK726": "Tharparkar",
  "PK727": "Thatta",
  "PK728": "Umer Kot",
  "PK729": "West Karachi",
};

export interface WeeklyTrendPoint {
  week: string;
  risk: number;
}

export interface DistrictRiskDataAPI {
  getRiskScore: (pcode: string, disease: DiseaseKey) => number;
  getWeeklyTrend: (pcode: string, disease: DiseaseKey) => Promise<WeeklyTrendPoint[]>;
}

/**
 * Real implementation using backend APIs
 */
export async function buildDistrictRiskData(pcodes: string[]): Promise<DistrictRiskDataAPI> {
  // Fetch latest risks for choropleth
  const latestRisks = await getAllDistrictRisks();

  const riskMap = new Map();
  latestRisks.forEach((item: any) => {
    const key = item.district_name?.toString().trim();
    if (key) {
      riskMap.set(key, {
        malaria: Number(item.risk_malaria) || 0,
        diarrhea: Number(item.risk_diarrhea) || 0,
        typhoid: Number(item.risk_typhoid) || 0,
      });
    }
  });

  return {
    getRiskScore(pcode: string, disease: DiseaseKey): number {
      // Map pcode to district_name, then lookup risk
      const districtName = pcodeToDistrict[pcode] || pcode;
      const data = riskMap.get(districtName);
      if (!data) return 0;
      return data[disease] || 0;
    },

    async getWeeklyTrend(pcode: string, disease: DiseaseKey): Promise<WeeklyTrendPoint[]> {
      try {
        // Convert pcode to district_name before calling backend
        const districtName = pcodeToDistrict[pcode] || pcode;
        const history = await getDistrictHistory(districtName, 12);
        return history.map((item: any) => ({
          week: item.week || `Week ${item.week_number || ''}`,
          risk: Number(item[`risk_${disease}`]) || 0,
        }));
      } catch (err) {
        console.error("Failed to fetch history for pcode", pcode, err);
        return [];
      }
    },
  };
}
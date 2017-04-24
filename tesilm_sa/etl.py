import mysql.connector

class Etl:
    
    # constants
    GENDER_MALE = 1
    GENDER_FEMA = 2
    PARTY_REPUB = 1
    PARTY_DEMOC = 2

    def __init__(self):
        self.cnx = mysql.connector.connect(user='olap_test', password='olap_test', database='olap_test')
        self.cursor = cnx.cursor()

    def put(self, obj):
        dTemp = obj["created_at"][4:10]+" "+obj["created_at"][-4:]
        saDate = self.__putDate(datetime.datetime.strptime(dTemp, "%b %d %Y").strftime('%Y-%m-%d'))
        saParty = PARTY_DEMOC if obj["affiliatedTo"][35:45] == "Democratic" else PARTY_REPUB
        saGender = GENDER_FEMA if obj["gender"][-6:] == "female" else GENDER_MALE
        saPolitician = self.__putPolitician({
                "name": obj["familyName"]+" "+obj["givenName"], 
                "dbpedia_resource": obj["dbpediaURI"],
                "gender_id": saGender,
                "party_id": saParty
                })["id"]
        sa1 = {"date_id": saDate,
                "politician_id": saPolitician,
                }
        return self.__putSentimentAnalysis(sa1, obj["sentiment_analysis"])
        
    def __putDate(self, date):
        self.cursor.execute("SELECT count(*) FROM dim_date WHERE date = %s ", [date])
        res = self.cursor.fetchone()
        if res[0] == 0:
            self.cursor.execute("INSERT INTO dim_date (date) VALUES (%s)", [date])
            self.cnx.commit()
        return date

    def __putPolitician(self, politician):
        self.cursor.execute("SELECT id FROM dim_politician WHERE dbpedia_resource = %s ", 
                [politician["dbpedia_resource"]])
        res = self.cursor.fetchone()
        if not res:
            self.cursor.execute("INSERT INTO dim_politician (name, dbpedia_resource, gender_id, party_id) "
                   "VALUES (%s, %s, %s, %s)", 
                   [politician["name"], politician["dbpedia_resource"], politician["gender_id"], politician["party_id"]])
            self.cnx.commit()
            politician["id"] = self.cursor.lastrowid
        else:
            politician["id"] = res[0]
        return politician

    def __putSentimentAnalysis(self, keys, sa):
        self.cursor.execute("SELECT id FROM fact_sentiment_analysis " 
                " WHERE date_id = %s AND politician_id = %s ", 
                [keys["date_id"], keys["politician_id"]])
        res = self.cursor.fetchone()
        if not res:
            self.cursor.execute("INSERT INTO fact_sentiment_analysis "
                "(date_id, politician_id, "+sa+") "
                "values (%s, %s, %s)",
                [keys["date_id"], keys["politician_id"], 1])
            self.cnx.commit()
            return self.cursor.lastrowid
        else:
            self.cursor.execute("UPDATE fact_sentiment_analysis SET " + sa + " = " + sa + " + 1 "
                    " WHERE id = %s",
                [res[0]])
            self.cnx.commit()
            return res[0]
        return False
    
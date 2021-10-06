// import * as React from 'react';
import React from 'react';
import Box from '@mui/material/Box';
import Slider from '@mui/material/Slider';
import axios from 'axios'
// import logo from './logo.svg';

import './App.css';

function valuetext(value) {
  return `${value}°C`;
}

const minDistance = 10;

function MinimumDistanceSlider() {

  const [value2, setValue2] = React.useState([20, 37]);

  const handleChange2 = (event, newValue, activeThumb) => {
    if (!Array.isArray(newValue)) {
      return;
    }

    if (newValue[1] - newValue[0] < minDistance) {
      if (activeThumb === 0) {
        const clamped = Math.min(newValue[0], 100 - minDistance);
        setValue2([clamped, clamped + minDistance]);
      } else {
        const clamped = Math.max(newValue[1], minDistance);
        setValue2([clamped - minDistance, clamped]);
      }
    } else {
      setValue2(newValue);
    }
  };

  return (
    <Box sx={{ width: 300 }}>
      <Slider
        getAriaLabel={() => 'Minimum distance shift'}
        value={value2}
        onChange={handleChange2}
        valueLabelDisplay="auto"
        getAriaValueText={valuetext}
        disableSwap
      />
    </Box>
  );
}

function ByDayTable(props) {
    // const [data, setData] = React.useState([]);

    // React.useEffect(() => {
    //     if (!('spd_rows' in props.data)) {
    //         return;
    //     }
    //     console.log(props.data)
    //     // setData(props.data['spd_rows']);
    //   }, [props.data]);

      // let data = props.data['spd_rows']
    return (
        <table className="cart">
        <thead>
            <tr>
            {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map((h,inx) =>
                <td key={inx}>{h}</td>
            )}
            </tr>
        </thead>

        <tbody>
            {props.data['spd_rows'] && props.data['spd_rows'].map((row,r_inx) =>
                <tr key={r_inx}>
                    {row.map((r, c_inx) => {
                        let [d,v,com] = r
                        if (d == null) {
                            return <td key={c_inx}/>
                        } else {
                            return (
                                <td key={c_inx} className="hasTooltip">{d} <br/>{v}
                                {com != null && <span className="tooltip" dangerouslySetInnerHTML={{__html: com}}/>}
                                </td>
                            )
                        }
                    })}
                </tr>
            )
            }
        </tbody>
    </table>
    );
}

function zip_longest() {
    var args = [].slice.call(arguments);
    var longest = args.reduce(function(a,b){
        return a.length>b.length ? a : b
    }, []);

    return longest.map(function(_,i){
        return args.map(function(array){return array[i]})
    });
}

function SummaryTable(props) {
    let data = props.data;
    return (
        <table className="cart">
        <thead>
            <tr>
                {data['headers'] && data['headers'].map((h, inx) => {
                    return <td key={inx}>{h}</td>
                })}
            </tr>
        </thead>

        <tbody>
            {data['rows'] && zip_longest(data['rows'], data['_com']).map((row_row_c, inx_r) => {
                let [row, row_c] = row_row_c
                return (
                    <tr key={inx_r}>
                        {zip_longest(row, row_c != null ? row_c : []).map((v_com, c_inx) => {
                            let [v,com] = v_com
                            return (
                                <td key={c_inx} className="hasTooltip">{v}
                                {com != null && <span className="tooltip" dangerouslySetInnerHTML={{__html: com}}/>}
                            </td>
                            )
                        })}
                    </tr>
                )
            })}
        </tbody>
    </table>
    )
}

function NavTable(props) {
    let data = props.data;

    const onLinkClick = (e) => {
        e.preventDefault();
        props.onLinkClick(e.target.href)
    };

    return (
        <table>
            <tbody>
                <tr>
                    <td> <a href={"/query?after="+data['prev_after']+"&before="+data['prev_before']} onClick={onLinkClick}>Prev Period {data['prev_after']} - {data['prev_before']}</a> </td>
                </tr>
                <tr>
                    <td> <a href={"/query?after="+data['next_after']+"&before="+data['next_before']} onClick={onLinkClick}>Next Period {data['next_after']} - {data['next_before']}</a> </td>
                </tr>
                <tr>
                    <td> <a href="/query" onClick={onLinkClick}>Last Period</a> </td>
                </tr>
                <tr>
                    <td> <a href="/upload" onClick={onLinkClick}>Upload</a> </td>
                </tr>
            </tbody>
        </table>
    )
}


function App() {
    const [data, setData] = React.useState({});
    const [query, setQuery] = React.useState("/query");
    React.useEffect(() => {
        const fetchData = async () => {
          const result = await axios(query);
            // console.log(result)
          setData(result.data);
        };
     
        fetchData();
      }, [query]);

  return (
    <div>
        <center>Summary {data['after']} - {data['before']}</center>
        <NavTable data={data} onLinkClick={setQuery} />
        <br/>
        <ByDayTable data={data}/>
        <br/><br/>
        <SummaryTable data={data}/>
    </div>
  );
}

export default App;

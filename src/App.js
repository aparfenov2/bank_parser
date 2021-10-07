// import * as React from 'react';
import React from 'react';
import Box from '@mui/material/Box';
import Slider from '@mui/material/Slider';
import Stack from '@mui/material/Stack';
import axios from 'axios'
// import logo from './logo.svg';

import {
    BrowserRouter as Router,
    Switch,
    Route,
    Link,
    useLocation,
    useHistory
} from "react-router-dom";

import './App.css';

function valuetext(value) {
    return new Date(new Date().setDate(new Date().getDate() + parseInt(value))).toDateString();
}

function MinimumDistanceSlider(props) {

    const minDistance = 1;
    // setValue2 = props.setValue

    const [value2, setValue2] = React.useState([-30, 0]);

    const [marks, setMarks] = React.useState([]);


    React.useEffect(() => {
        const fetchData = async () => {
            const result = await axios("/ranges");
            setMarks(result.data.ranges.map(d => {
                return {
                    value: d,
                    label: valuetext(d)
                }
            }));
        };
        fetchData();
    }, []);

    const handleChange2 = (event, newValue, activeThumb) => {
        if (!Array.isArray(newValue)) {
            return;
        }

        if (Math.abs(newValue[1] - newValue[0]) < minDistance) {
            if (activeThumb === 0) {
                const clamped = Math.min(newValue[0], 0 - minDistance);
                setValue2([clamped, clamped + minDistance]);
            } else {
                const clamped = Math.max(newValue[1], -124 + minDistance);
                setValue2([clamped - minDistance, clamped]);
            }
        } else {
            setValue2(newValue);
        }
    };

    return (
        <Slider
            getAriaLabel={() => 'Minimum distance shift'}
            value={value2}
            min={-124}
            max={0}
            marks={marks}
            onChange={handleChange2}
            valueLabelDisplay="on"
            valueLabelFormat={valuetext}
            disableSwap
        />
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
                    {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((h, inx) =>
                        <td key={inx}>{h}</td>
                    )}
                </tr>
            </thead>

            <tbody>
                {props.data['spd_rows'] && props.data['spd_rows'].map((row, r_inx) =>
                    <tr key={r_inx}>
                        {row.map((r, c_inx) => {
                            let [d, v, com] = r
                            if (d == null) {
                                return <td key={c_inx} />
                            } else {
                                return (
                                    <td key={c_inx} className="hasTooltip">{d} <br />{v}
                                        {com != null && <span className="tooltip" dangerouslySetInnerHTML={{ __html: com }} />}
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
    var longest = args.reduce(function (a, b) {
        return a.length > b.length ? a : b
    }, []);

    return longest.map(function (_, i) {
        return args.map(function (array) { return array[i] })
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
                                let [v, com] = v_com
                                return (
                                    <td key={c_inx} className="hasTooltip">{v}
                                        {com != null && <span className="tooltip" dangerouslySetInnerHTML={{ __html: com }} />}
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

    return (
        <table width="100%">
            <tbody>
                <tr>
                    <td> <Link to={"?after=" + data['prev_after'] + "&before=" + data['prev_before']} onClick={props.onLinkClick}>Prev Period {data['prev_after']} - {data['prev_before']}</Link> </td>
                </tr>
                <tr>
                    <td> <Link to={"?after=" + data['next_after'] + "&before=" + data['next_before']} onClick={props.onLinkClick}>Next Period {data['next_after']} - {data['next_before']}</Link> </td>
                </tr>
                <tr>
                    <td> <Link to="/" onClick={props.onLinkClick}>Last Period</Link> </td>
                </tr>
                <tr>
                    <td> <Link to="/upload">Upload</Link> </td>
                </tr>
            </tbody>
        </table>
    )
}


function Home() {
    let location = useLocation();
    let query_args = Object.fromEntries(new URLSearchParams(location.search));

    const [ajax_data, setData] = React.useState(query_args);
    const [ajax_query, setQuery] = React.useState("/query" + location.search);

    const onLinkClick = (e) => {
        // e.preventDefault();
        setQuery("/query" + e.target.search)
    };

    React.useEffect(() => {
        const fetchData = async () => {
            const result = await axios(ajax_query);
            setData(result.data);
        };

        fetchData();
    }, [ajax_query, location]);

    return (
        <Stack spacing={3}>
            <center>Summary {ajax_data['after']} - {ajax_data['before']}</center>
            <Stack direction="row" spacing={1}>
                <Box width={600}>
                    <NavTable data={ajax_data} onLinkClick={onLinkClick} />
                </Box>
                <MinimumDistanceSlider />
                <Box sx={{ width: 100 }}/>
            </Stack>
            <ByDayTable data={ajax_data} />
            <SummaryTable data={ajax_data} />
        </Stack>
    );
}


function Upload() {
    return (
        <a>Not Implemented</a>
    );
}

function App() {
    return (
        <Router>
            <Switch>
                <Route path="/upload">
                        <Upload/>
                    </Route>
                <Route path="/">
                    <Home/>
                </Route>
            </Switch>
        </Router>
    );
}

export default App;

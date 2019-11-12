import * as d3 from "d3"


// membership data - defined in the global scope outside this module, in the template
type MembershipCount = {
    count: number,
    startDate: string,
}
type MembershipCountArray = Array<MembershipCount>

type MembershipTotals = {
    cards: MembershipCountArray,
    logbooks: MembershipCountArray,
    members: MembershipCountArray,
}

declare const membershipData: MembershipTotals

// <div class="timeline" data-series="subscriptions borrows members">
const targets = document.getElementsByClassName('membership-graph') as HTMLCollection

const bookstoreDates = {
    start: new Date(1919, 1, 1),
    end: new Date(1942, 12, 31)
}

const svgheight = 280;

const x = d3.scaleTime()
    // whole timeline
    .domain([bookstoreDates.start, bookstoreDates.end])
    .range([0, 911]);  // ??

const xAxis = d3.axisTop(x);


Array.from(targets).forEach((el: HTMLDivElement) => {
    drawMembershipGraph(el);
});


function drawMembershipGraph(el: HTMLDivElement) {

    // use data-series attribute to determine which data to show
    // if not set, could be empty string or null depending on the browser
    const dataSeries = el.getAttribute('data-series')

    const svg = d3.select(el).append('svg')
        .attr('preserveAspectRatio', 'xMidYMid meet')
        .attr('viewBox', '0 0 905 285')
        .attr('aria-label', 'Chart: Membership Graph')
        .attr('role', 'img')

    svg.append("g")
        .attr("transform", "translate(10,30)")
        .call(xAxis)
        .call(g => g.selectAll(".tick line")
            .attr("stroke", '#231F20')
            .attr("stroke-width", '0.25')
            .attr('stroke-dasharray', '2,2')
            .attr("y2", 250)
            .attr("y1", 0))
        // remove domain path automatically added by d3 axis
        .call(g => g.select(".domain").remove())

    const maxCount = membershipData.logbooks.map(d => d.count).reduce(function(a, b) {
        return Math.max(a, b);
    });

    const y = d3.scaleLinear()
      .domain([maxCount, 0])
      .range([0, 280]);

    const yAxis = d3.axisRight(y)
      .ticks(5)
      .tickSize(0);

    svg.append("g")
        .call(yAxis)
      // remove domain path automatically added by d3 axis
      .call(g => g.select(".domain").remove())

    if (dataSeries && dataSeries.includes('borrows')) {
        svg.append('g')
            .attr("transform", "translate(10,0)")
            .attr('class', 'borrowing-bars')
          .selectAll('bar')
          .data(membershipData.cards.filter(event => (new Date(event.startDate) < bookstoreDates.end)))
          .join(
            enter => enter.append("rect")
                            .attr('class', 'borrowing')
                            .attr('x', function(d) {
                              return x(new Date(d.startDate))
                             })
                            .attr('y', function (d) {
                                return svgheight - d.count
                            })
                            .attr("fill", "#47C2C2")
                            .attr("opacity", "0.8")
                            .attr("width", 2.35)
                            .attr("height",function (d) {
                                return d.count
                         })
            )
      }

    if (dataSeries && dataSeries.includes('subscriptions')) {
        svg.append('g')
            .attr('class', 'subscription-bars')
            .attr("transform", "translate(10,0)")
          .selectAll('bar')
          .data(membershipData.logbooks)
          .join(
                enter => enter.append("rect")
                    .attr('class', 'subscription')
                    .attr('x', function(d) {
                      return x(new Date(d.startDate))
                     })
                    .attr('y', function (d) {
                        return svgheight - d.count
                    })
                    .attr("fill", "#231F20")
                    .attr("opacity", "0.2")
                    .attr("width", 2.35)
                    .attr("height",function (d) {
                        return d.count
                })
          )
    }

    if (dataSeries && dataSeries.includes('members')) {
        svg.append('g')
            .attr('class', 'member-bars')
            .attr("transform", "translate(10,0)")
          .selectAll('bar')
          .data(membershipData.members)
          .join(
                enter => enter.append("rect")
                    .attr('class', 'members')
                    .attr('x', function(d) {
                      return x(new Date(d.startDate))
                     })
                    .attr('y', function (d) {
                        return svgheight - d.count
                    })
                    .attr("fill", "#8a8a8a")
                    .attr("opacity", "0.2")
                    .attr("width", 2.35)
                    .attr("height",function (d) {
                        return d.count
                     })
            )
    }
}
